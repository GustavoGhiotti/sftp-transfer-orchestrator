"""Repositório de registro — TB_TRANSFERENCIAS (DB_SFTP).

Garante a idempotência: sabe o que já foi transferido e registra o novo.
"""

from datetime import date

from src.infrastructure.database.executor import Executor


class RepoTransferencias:
    def __init__(self, conexao: dict):
        self.executor = Executor(**conexao)

    def ja_transferiu_hoje(self, id_mapa: int) -> bool:
        """True se este mapa já registrou um arquivo com data de HOJE.
        Usado para pular o mapa (sem nem conectar na origem) quando o
        arquivo do dia já foi transferido — cenário do agendador 10/10min."""
        query = """
            SELECT TOP 1 1 AS existe
            FROM TB_TRANSFERENCIAS WITH (NOLOCK)
            WHERE ID_MAPA = ? AND DT_ARQUIVO = ?
        """
        linha = self.executor.executar_query(
            query=query, parametros=[id_mapa, date.today().isoformat()], fetch="one"
        )
        return linha is not None

    def nomes_ja_transferidos(self, id_mapa: int) -> set[str]:
        """Nomes de arquivo já transferidos para este mapa (para filtrar pendentes)."""
        query = """
            SELECT NM_ARQUIVO
            FROM TB_TRANSFERENCIAS WITH (NOLOCK)
            WHERE ID_MAPA = ?
        """
        linhas = self.executor.executar_query(query=query, parametros=[id_mapa], fetch="all")
        return {linha["NM_ARQUIVO"] for linha in linhas} if linhas else set()

    def registrar(
        self,
        *,
        id_mapa: int,
        id_cedente: int,
        nm_arquivo: str,
        dt_arquivo: date | None,
        tamanho_bytes: int | None,
    ) -> None:
        """Registra 1 arquivo transferido. A UNIQUE (ID_MAPA, NM_ARQUIVO, DT_ARQUIVO)
        protege contra duplicidade mesmo em execuções concorrentes."""
        query = """
            INSERT INTO TB_TRANSFERENCIAS
                (ID_MAPA, ID_CEDENTE, NM_ARQUIVO, DT_ARQUIVO, TAMANHO_BYTES)
            VALUES (?, ?, ?, ?, ?)
        """
        # O driver legado "SQL Server" não faz bind de datetime.date;
        # envia como texto ISO (YYYY-MM-DD) e o SQL Server converte p/ DATE.
        dt_texto = dt_arquivo.isoformat() if dt_arquivo is not None else None
        self.executor.executar_query(
            query=query,
            parametros=[
                int(id_mapa),
                int(id_cedente),
                nm_arquivo,
                dt_texto,
                int(tamanho_bytes) if tamanho_bytes is not None else None,
            ],
        )
