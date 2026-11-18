"""Entidade ResultadoTransferencia — o que um processo (mapa) produziu.

Alimenta o registro (TB_TRANSFERENCIAS, feito no serviço) e o log
(TB_LOG_EXECUCAO, feito pelo orquestrador).
"""

from dataclasses import dataclass, field
from datetime import datetime

STATUS_SUCESSO = "SUCESSO"
STATUS_ERRO = "ERRO"
STATUS_SEM_ARQUIVOS = "SEM_ARQUIVOS"


@dataclass
class ResultadoTransferencia:
    id_mapa: int
    id_cedente: int
    nm_cedente: str
    dt_inicio: datetime
    dt_fim: datetime | None = None
    status: str = STATUS_SEM_ARQUIVOS
    qtd_arquivos: int = 0
    nm_arquivos: list[str] = field(default_factory=list)
    mensagem: str | None = None

    def nomes_como_texto(self) -> str | None:
        return "; ".join(self.nm_arquivos) if self.nm_arquivos else None
