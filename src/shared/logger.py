"""Logger central — arquivo rotativo + console.

Log técnico/operacional em arquivo. O log de negócio (TB_LOG_EXECUCAO) é
responsabilidade do repo_logs, não deste módulo.

Uso:
    from src.shared.logger import get_logger
    log = get_logger(__name__)
    log.info("mensagem")
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_PASTA_LOGS = Path(__file__).resolve().parents[2] / "logs"
_ARQUIVO_LOG = _PASTA_LOGS / "robo.log"
_FORMATO = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Bibliotecas barulhentas: só ERRO (o robô loga o que importa em INFO).
_LIBS_SILENCIOSAS = ("paramiko", "smbprotocol", "smbclient")

_configurado = False


def _configurar() -> None:
    global _configurado
    if _configurado:
        return

    os.makedirs(_PASTA_LOGS, exist_ok=True)

    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)

    # Rotaciona todo dia à meia-noite e mantém só 7 dias (o resto é apagado).
    # Os arquivos antigos recebem a data no nome (ex.: robo.log.2026-09-02).
    arquivo = TimedRotatingFileHandler(
        _ARQUIVO_LOG, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    arquivo.suffix = "%Y-%m-%d"
    arquivo.setFormatter(logging.Formatter(_FORMATO))
    raiz.addHandler(arquivo)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMATO))
    raiz.addHandler(console)

    # Silencia as bibliotecas de rede: mostra só ERRO delas.
    for lib in _LIBS_SILENCIOSAS:
        logging.getLogger(lib).setLevel(logging.ERROR)

    _configurado = True


def get_logger(nome: str) -> logging.Logger:
    _configurar()
    return logging.getLogger(nome)
