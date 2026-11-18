"""Cliente SMB concreto (smbclient) — implementa IOrigem E IDestino.

Sabe LER/listar (papel de origem) e GRAVAR/criar pasta (papel de destino),
para que o SMB possa ser tanto a fonte quanto o alvo de um processo.

CONCORRÊNCIA: a conexão SMB do smbprotocol NÃO é thread-safe (o controle de
"créditos" do SMB2 dá conflito entre threads na mesma conexão). Por isso cada
THREAD usa a sua própria conexão, via um connection_cache thread-local. Assim
o pool paralelo (MAX_WORKERS) funciona sem o erro "requires 1 credits...".

Credenciais são por servidor (extraído do caminho UNC): a sessão de cada
servidor é registrada uma vez POR THREAD, sob demanda.
"""

import ntpath
import threading
from datetime import date, datetime
from time import sleep

import smbclient

from src.shared.exceptions import ConfiguracaoInvalida
from src.shared.logger import get_logger

log = get_logger(__name__)

_local = threading.local()


def _extrair_servidor(caminho: str) -> str:
    r"""\\10.0.0.64\share\x -> 10.0.0.64."""
    return caminho.strip().lstrip("\\").split("\\")[0]


class SMBClient:
    def __init__(self, smb_por_servidor: dict):
        self._smb = smb_por_servidor  # {servidor: {usuario, senha}}

    # ---- conexão por thread ------------------------------------------
    def _cache(self) -> dict:
        cache = getattr(_local, "cache", None)
        if cache is None:
            cache = {}
            _local.cache = cache
            _local.registrados = set()
        return cache

    def _preparar(self, caminho: str) -> dict:
        """Garante a sessão do servidor do caminho registrada NESTA thread."""
        cache = self._cache()
        servidor = _extrair_servidor(caminho)
        if servidor not in _local.registrados:
            cred = self._smb.get(servidor)
            if not cred:
                raise ConfiguracaoInvalida(
                    f"Sem credencial SMB configurada para o servidor {servidor} "
                    f"(verifique SMB_SERVERS e SMB_<octeto>_USER/_PASSWORD no .env)"
                )
            smbclient.register_session(
                server=servidor,
                username=cred["usuario"],
                password=cred["senha"],
                connection_cache=cache,
            )
            _local.registrados.add(servidor)
            log.info("Sessão SMB registrada em %s (thread %s)", servidor, threading.get_ident())
        return cache

    def conectar(self) -> None:
        """Sessão é por thread e sob demanda; nada a fazer aqui."""

    # ---- papel de ORIGEM (leitura) -----------------------------------
    def listar_arquivos_com_info(self, caminho: str) -> list[dict]:
        cache = self._preparar(caminho)
        arquivos = []
        for item in smbclient.scandir(caminho, connection_cache=cache):
            if not item.is_file():
                continue
            info = item.stat()
            arquivos.append(
                {
                    "nome": item.name,
                    "bytes": info.st_size,
                    "mtime": datetime.fromtimestamp(info.st_mtime),
                    "data": date.fromtimestamp(info.st_mtime),
                }
            )
        return arquivos

    def abrir_leitura(self, caminho: str):
        cache = self._preparar(caminho)
        return smbclient.open_file(caminho, mode="rb", connection_cache=cache)

    def validar_arquivo_pronto(self, caminho: str, tentativas: int = 3, espera: int = 15) -> bool:
        cache = self._preparar(caminho)
        ultimo = -1
        for _ in range(tentativas):
            atual = smbclient.stat(caminho, connection_cache=cache).st_size
            if atual == ultimo:
                return True
            ultimo = atual
            sleep(espera)
        return False

    # ---- papel de DESTINO (escrita) ----------------------------------
    def criar_diretorio(self, caminho_arquivo: str) -> None:
        cache = self._preparar(caminho_arquivo)
        pasta = ntpath.dirname(caminho_arquivo)
        if pasta:
            smbclient.makedirs(pasta, exist_ok=True, connection_cache=cache)

    def abrir_escrita(self, caminho: str):
        cache = self._preparar(caminho)
        return smbclient.open_file(caminho, mode="wb", connection_cache=cache)

    def existe(self, caminho: str) -> bool:
        cache = self._preparar(caminho)
        try:
            smbclient.stat(caminho, connection_cache=cache)
            return True
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def join_path(pasta: str, nome: str) -> str:
        return ntpath.join(pasta.rstrip("\\/"), nome)

    # ---- context manager (conexão vive na thread; nada a fechar aqui) -
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def close(self) -> None:
        return None
