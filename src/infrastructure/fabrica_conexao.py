r"""Fábrica de conexões — DETECTA SFTP ou SMB pelo formato do caminho.

Sem coluna de tipo: o próprio caminho diz o protocolo.
  - SMB   -> caminho UNC, começa com '\\' (ex.: \\10.0.0.64\arquivos\...).
  - SFTP  -> qualquer outro (ex.: /saida, pasta/sub).

Regra de credencial (independe do sentido do processo):
  - SFTP  -> credencial do CEDENTE (colunas vindas de TB_CONEXAO_SFTP no mapa).
  - SMB   -> credencial do SERVIDOR extraído do próprio caminho UNC. Há vários
             SMB (ex.: .64, .71, .72), cada um com seu usuário/senha; a sessão
             de cada servidor é registrada uma única vez no processo.

Assim o mesmo mapa suporta qualquer combinação: SFTP->SMB, SMB->SFTP,
SMB->SMB e SFTP->SFTP — decidido só pelos caminhos ORIGEM e DESTINO.
"""

import re

from src.config.settings import resolver_chave
from src.infrastructure.sftp.sftp_client import SFTPClient
from src.infrastructure.smb.smb_client import SMBClient

TIPO_SFTP = "SFTP"
TIPO_SMB = "SMB"


def detectar_tipo(caminho: str) -> str:
    """SMB se o caminho for UNC (começa com '\\'); caso contrário, SFTP."""
    return TIPO_SMB if (caminho or "").strip().startswith("\\\\") else TIPO_SFTP


def extrair_servidor_smb(caminho: str) -> str:
    r"""Extrai o servidor de um caminho UNC: \\10.0.0.64\share\x -> 10.0.0.64."""
    return caminho.strip().lstrip("\\").split("\\")[0]


def _componentes(caminho: str) -> list[str]:
    """Quebra o caminho em partes, sem barras/servidor de UNC no começo."""
    c = (caminho or "").strip().lstrip("\\/")
    return [p for p in re.split(r"[\\/]+", c) if p]


def resolver_credenciais_sftp(senha: str | None, arquivo_chave: str | None) -> tuple:
    """Decide entre senha e chave para o SFTP e devolve (password, key_file).

    Conveniência: se ARQUIVO_CHAVE estiver vazio mas SENHA terminar em '.pem',
    o robô trata a SENHA como o NOME/caminho da chave (não como senha).
    ARQUIVO_CHAVE explícito tem prioridade. O nome é resolvido em chaves/.
    """
    chave = arquivo_chave
    if (not chave or not chave.strip()) and senha and senha.strip().lower().endswith(".pem"):
        chave = senha
        senha = None
    return senha, resolver_chave(chave)


def redirecionar_destino(destino_real: str, base_teste: str) -> str:
    r"""Redireciona o destino para a base de teste, PRESERVANDO a estrutura
    (servidor + share + subpastas) por baixo dela, para não colidir arquivos
    de mapas diferentes. O separador segue o tipo da base de teste.

    Ex.: \\10.0.0.64\arquivos\entrada  +  base \\10.0.0.72\teste
      -> \\10.0.0.72\teste\10.0.0.64\arquivos\entrada
    """
    base = base_teste.strip().rstrip("\\/")
    sep = "\\" if detectar_tipo(base) == TIPO_SMB else "/"
    comps = _componentes(destino_real)
    return f"{base}{sep}{sep.join(comps)}" if comps else base


class FabricaConexao:
    def __init__(self, smb_por_servidor: dict):
        self._smb = smb_por_servidor  # {servidor: {usuario, senha}}

    def criar_origem(self, mapa: dict):
        return self._criar(mapa["ORIGEM"], mapa)

    def criar_destino(self, mapa: dict):
        return self._criar(mapa["DESTINO"], mapa)

    # ------------------------------------------------------------------
    def _criar(self, caminho: str, mapa: dict):
        if detectar_tipo(caminho) == TIPO_SFTP:
            return self._sftp(mapa)
        # O SMBClient registra a sessão do servidor por thread, sob demanda.
        return SMBClient(self._smb)

    @staticmethod
    def _sftp(mapa: dict) -> SFTPClient:
        password, key_file = resolver_credenciais_sftp(
            mapa.get("SENHA"), mapa.get("ARQUIVO_CHAVE")
        )
        return SFTPClient(
            hostname=mapa["HOSTNAME"],
            user=mapa["USUARIO"],
            port=mapa.get("PORTA_HOST") or 22,
            password=password,
            key_file=key_file,
        )
