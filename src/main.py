"""Ponto de entrada do robô.

Chamado pelo agendador do Windows a cada 10 min (via start/run.bat).
Apenas dispara o Orquestrador; nenhuma regra de negócio vive aqui.
"""

from src.application.orquestrador import Orquestrador
from src.shared.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    log.info("=== Início da execução ===")
    try:
        Orquestrador().executar()
    except Exception:
        log.exception("Falha não tratada na execução")
        raise
    finally:
        log.info("=== Fim da execução ===")


if __name__ == "__main__":
    main()
