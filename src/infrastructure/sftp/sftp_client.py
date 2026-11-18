"""Cliente SFTP concreto (paramiko) — implementa IOrigem E IDestino.

Sabe LER/listar (papel de origem) e GRAVAR/criar pasta (papel de destino),
para que o SFTP possa ser tanto a fonte quanto o alvo de um processo.
Conexão com retry/backoff e reconexão em sessão expirada. Suporta
autenticação por senha OU por chave privada (.pem).
Baseado no padrão validado no RoboCargas (server/conexao_sftp.py).
"""

import posixpath
import stat
from datetime import date, datetime
from time import sleep

from paramiko import AutoAddPolicy, RSAKey, SSHClient
from paramiko.ssh_exception import SSHException

from src.shared.exceptions import ConexaoError
from src.shared.logger import get_logger

log = get_logger(__name__)

_MAX_TENTATIVAS = 5
_ESPERA_SEG = 3


class SFTPClient:
    def __init__(
        self,
        hostname: str,
        user: str,
        port: int = 22,
        password: str | None = None,
        key_file: str | None = None,
    ):
        self.hostname = hostname
        self.user = user
        self.port = port or 22
        self.password = password
        self.key_file = key_file
        self._ssh: SSHClient | None = None
        self._sftp = None
        self._connect()

    def _connect(self) -> None:
        self.close()
        for tentativa in range(1, _MAX_TENTATIVAS + 1):
            try:
                pkey = RSAKey.from_private_key_file(self.key_file) if self.key_file else None
                ssh = SSHClient()
                ssh.set_missing_host_key_policy(AutoAddPolicy())
                ssh.connect(
                    hostname=self.hostname,
                    username=self.user,
                    password=self.password,
                    port=self.port,
                    pkey=pkey,
                    look_for_keys=False,
                    allow_agent=False,
                    timeout=15,
                )
                self._ssh = ssh
                self._sftp = ssh.open_sftp()
                self._ssh.get_transport().set_keepalive(7)
                log.info("Conectado ao SFTP %s:%s", self.hostname, self.port)
                return
            except Exception as exc:  # noqa: BLE001 - loga e tenta de novo
                log.warning(
                    "Falha SFTP %s (tentativa %s/%s): %s",
                    self.hostname, tentativa, _MAX_TENTATIVAS, exc,
                )
                if tentativa < _MAX_TENTATIVAS:
                    sleep(_ESPERA_SEG)
        raise ConexaoError(f"Não foi possível conectar ao SFTP {self.hostname}")

    def listar_arquivos_com_info(self, caminho: str) -> list[dict]:
        """Lista arquivos regulares da pasta com nome, tamanho e data (mtime)."""
        try:
            itens = self._sftp.listdir_attr(caminho)
        except (SSHException, OSError):
            log.info("Sessão SFTP expirada ao listar %s; reconectando...", caminho)
            self._connect()
            itens = self._sftp.listdir_attr(caminho)

        arquivos = []
        for item in itens:
            if not stat.S_ISREG(item.st_mode):
                continue
            arquivos.append(
                {
                    "nome": item.filename,
                    "bytes": item.st_size,
                    "mtime": datetime.fromtimestamp(item.st_mtime),
                    "data": date.fromtimestamp(item.st_mtime),
                }
            )
        return arquivos

    def abrir_leitura(self, caminho: str):
        """Handle de leitura binária (papel de ORIGEM)."""
        return self._abrir(caminho, "rb")

    def abrir_escrita(self, caminho: str):
        """Handle de escrita binária (papel de DESTINO)."""
        return self._abrir(caminho, "wb")

    def _abrir(self, caminho: str, modo: str):
        try:
            return self._sftp.open(caminho, modo)
        except (SSHException, OSError):
            log.info("Sessão SFTP expirada ao abrir %s; reconectando...", caminho)
            self._connect()
            return self._sftp.open(caminho, modo)

    def criar_diretorio(self, caminho_arquivo: str) -> None:
        """Garante que a pasta do arquivo de destino existe (mkdir -p remoto)."""
        pasta = posixpath.dirname(caminho_arquivo)
        if not pasta or pasta == "/":
            return
        raiz = "/" if pasta.startswith("/") else ""
        atual = raiz
        for parte in pasta.strip("/").split("/"):
            atual = posixpath.join(atual, parte) if atual else parte
            try:
                self._sftp.stat(atual)
            except (SSHException, OSError):
                self._sftp.mkdir(atual)

    def existe(self, caminho: str) -> bool:
        try:
            self.stat(caminho)
            return True
        except (SSHException, OSError):
            return False

    @staticmethod
    def join_path(pasta: str, nome: str) -> str:
        return posixpath.join(pasta, nome)

    def stat(self, caminho: str):
        try:
            return self._sftp.stat(caminho)
        except (SSHException, OSError):
            self._connect()
            return self._sftp.stat(caminho)

    def validar_arquivo_pronto(self, caminho: str, tentativas: int = 3, espera: int = 15) -> bool:
        """Confere se o tamanho está estável (arquivo não está em upload)."""
        ultimo = -1
        for _ in range(tentativas):
            atual = self._sftp.stat(caminho).st_size
            if atual == ultimo:
                return True
            ultimo = atual
            sleep(espera)
        return False

    def reconect(self) -> None:
        self._connect()

    def close(self) -> None:
        if self._sftp is not None:
            try:
                self._sftp.close()
            except Exception:  # noqa: BLE001
                pass
            self._sftp = None
        if self._ssh is not None:
            try:
                self._ssh.close()
            except Exception:  # noqa: BLE001
                pass
            self._ssh = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
