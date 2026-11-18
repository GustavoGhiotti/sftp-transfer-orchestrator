"""Repositório de configuração — TB_CONEXAO_SFTP e TB_ARQUIVO_MAPA (DB_SFTP).

Lê as credenciais e os mapas ativos. Vínculo por ID_CEDENTE.
"""

from src.infrastructure.database.executor import Executor


class RepoConfig:
    def __init__(self, conexao: dict):
        self.executor = Executor(**conexao)

    def listar_mapas_ativos(self) -> list[dict]:
        """Todos os mapas ativos cujo cedente também está ativo (com dados da conexão)."""
        query = """
            SELECT
                m.ID              AS ID_MAPA,
                m.ID_CEDENTE      AS ID_CEDENTE,
                m.DESCRICAO       AS DESCRICAO,
                m.ORIGEM          AS ORIGEM,
                m.DESTINO         AS DESTINO,
                m.PADRAO_ARQUIVO  AS PADRAO_ARQUIVO,
                m.SOMENTE_HOJE    AS SOMENTE_HOJE,
                m.RENOMEAR_COM_DATA AS RENOMEAR_COM_DATA,
                c.NM_CEDENTE      AS NM_CEDENTE,
                c.HOSTNAME        AS HOSTNAME,
                c.USUARIO         AS USUARIO,
                c.SENHA           AS SENHA,
                c.ARQUIVO_CHAVE   AS ARQUIVO_CHAVE,
                c.PORTA_HOST      AS PORTA_HOST,
                c.TIPO_PROTOCOLO  AS TIPO_PROTOCOLO
            FROM TB_ARQUIVO_MAPA m WITH (NOLOCK)
            INNER JOIN TB_CONEXAO_SFTP c WITH (NOLOCK)
                ON c.ID_CEDENTE = m.ID_CEDENTE
            WHERE m.ATIVO = 1 AND c.ATIVO = 1
            ORDER BY m.ID_CEDENTE, m.ID
        """
        return self.executor.executar_query(query=query, fetch="all")

    def obter_credencial(self, id_cedente: int) -> dict | None:
        query = """
            SELECT ID_CEDENTE, NM_CEDENTE, HOSTNAME, USUARIO, SENHA,
                   ARQUIVO_CHAVE, PORTA_HOST, TIPO_PROTOCOLO
            FROM TB_CONEXAO_SFTP WITH (NOLOCK)
            WHERE ID_CEDENTE = ? AND ATIVO = 1
        """
        return self.executor.executar_query(query=query, parametros=[id_cedente], fetch="one")
