"""Carrega variáveis de ambiente (.env) e constantes do robô.

Segredos NUNCA no código: tudo vem do .env (ver .env.example).
Expõe as configurações de forma tipada para as demais camadas.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.shared.exceptions import ConfiguracaoInvalida

load_dotenv()

# Raiz do projeto (…/src/config/settings.py -> sobe 2 níveis).
_RAIZ = Path(__file__).resolve().parents[2]

# Pasta das chaves .pem, DENTRO do robô por padrão (pode trocar via .env).
PASTA_CHAVES: Path = Path(os.getenv("PASTA_CHAVES") or (_RAIZ / "chaves"))


def resolver_chave(arquivo_chave: str | None) -> str | None:
    """Resolve o caminho do .pem. Se ARQUIVO_CHAVE for só o nome do arquivo,
    procura em PASTA_CHAVES (chaves/ dentro do robô); se for caminho absoluto,
    usa como está. Vazio/None -> None (autentica por senha)."""
    if not arquivo_chave or not arquivo_chave.strip():
        return None
    caminho = Path(arquivo_chave.strip())
    if not caminho.is_absolute():
        caminho = PASTA_CHAVES / caminho
    return str(caminho)


def _obrigatoria(nome: str) -> str:
    """Lê uma variável obrigatória; falha cedo e claro se faltar."""
    valor = os.getenv(nome)
    if valor is None or valor.strip() == "":
        raise ConfiguracaoInvalida(f"Variável de ambiente obrigatória ausente: {nome}")
    return valor.strip()


def _bool_env(nome: str, default: bool = False) -> bool:
    valor = os.getenv(nome)
    if valor is None or valor.strip() == "":
        return default
    return valor.strip().lower() in ("1", "true", "sim", "yes", "y", "s")


def conexao_sftp_db() -> dict:
    """Banco de configuração (DB_SFTP). Usa o usuário ÚNICO do banco."""
    return _conexao_db(_obrigatoria("DB_SFTP_DATABASE"))


def conexao_logs_db() -> dict:
    """Banco de logs (LOGS_ROBOS). Usa o mesmo usuário único do banco."""
    return _conexao_db(_obrigatoria("DB_LOGS_DATABASE"))


def _conexao_db(banco: str) -> dict:
    """Servidor e usuário são únicos (1 credencial para todas as tabelas);
    só o nome do banco muda entre configuração e logs."""
    return {
        "ipServidor": _obrigatoria("DB_SERVER"),
        "banco": banco,
        "usuario": _obrigatoria("DB_USER"),
        "senha": _obrigatoria("DB_PASSWORD"),
    }


def credenciais_smb_por_servidor() -> dict:
    """Mapa {servidor: {usuario, senha}} para cada SMB configurado.

    SMB_SERVERS lista os IPs (ex.: 10.0.0.64,10.0.0.71,10.0.0.72).
    Para cada um, lê SMB_<ultimo_octeto>_USER / _PASSWORD
    (ex.: SMB_64_USER, SMB_64_PASSWORD).
    """
    servidores = [s.strip() for s in _obrigatoria("SMB_SERVERS").split(",") if s.strip()]
    creds: dict[str, dict] = {}
    for servidor in servidores:
        octeto = servidor.split(".")[-1]
        creds[servidor] = {
            "usuario": _obrigatoria(f"SMB_{octeto}_USER"),
            "senha": _obrigatoria(f"SMB_{octeto}_PASSWORD"),
        }
    return creds


# Execução (com defaults sensatos)
MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
CHUNK_MB: int = int(os.getenv("CHUNK_MB", "64"))

# Verificação "arquivo pronto" (tamanho estável antes de baixar):
# quantas checagens e quantos segundos entre elas. Total ~= tentativas * espera.
TENTATIVAS_ARQUIVO: int = int(os.getenv("TENTATIVAS_ARQUIVO", "3"))
ESPERA_ARQUIVO_SEG: int = int(os.getenv("ESPERA_ARQUIVO_SEG", "15"))

# Modo de teste: quando ligado, os DESTINOS são redirecionados para
# DESTINO_TESTE (a tabela não muda; a origem continua a real).
MODO_TESTE: bool = _bool_env("MODO_TESTE", False)


def destino_teste() -> str:
    """Base de destino usada quando MODO_TESTE está ligado."""
    return _obrigatoria("DESTINO_TESTE")
