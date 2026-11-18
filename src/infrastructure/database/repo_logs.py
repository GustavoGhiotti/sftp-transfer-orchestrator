"""Repositório de logs — LOGS_ROBOS.TB_LOG_EXECUCAO.

Grava 1 linha por processo/mapa executado. ID_EXECUCAO agrupa o disparo.
"""

from datetime import datetime

from src.infrastructure.database.executor import Executor


class RepoLogs:
    def __init__(self, conexao: dict):
        self.executor = Executor(**conexao)

    def registrar_execucao(
        self,
        *,
        id_execucao: str,
        id_mapa: int | None,
        id_cedente: int | None,
        nm_cedente: str | None,
        dt_inicio: datetime,
        dt_fim: datetime | None,
        status: str,
        qtd_arquivos: int,
        nm_arquivos: str | None,
        mensagem: str | None,
        maquina: str | None,
    ) -> None:
        query = """
            INSERT INTO TB_LOG_EXECUCAO
                (ID_EXECUCAO, ID_MAPA, ID_CEDENTE, NM_CEDENTE, DT_INICIO, DT_FIM,
                 STATUS, QTD_ARQUIVOS, NM_ARQUIVOS, MENSAGEM, MAQUINA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.executor.executar_query(
            query=query,
            parametros=[
                id_execucao, id_mapa, id_cedente, nm_cedente, dt_inicio, dt_fim,
                status, qtd_arquivos, nm_arquivos, mensagem, maquina,
            ],
        )
