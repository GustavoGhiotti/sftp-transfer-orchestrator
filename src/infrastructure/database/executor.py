"""Executor de queries SQL Server (pyodbc) — genérico.

Usado tanto pelo banco de configuração (DB_SFTP) quanto pelo de logs
(LOGS_ROBOS); cada um instancia com o seu dicionário de conexão.

Evolução do executor do RoboCargas: abre/fecha a conexão por query, com
tratamento de erro que não estoura no finally.
"""

import os
from typing import Any, List, Optional

import pyodbc

from src.shared.exceptions import ConexaoError
from src.shared.logger import get_logger

log = get_logger(__name__)

# Ordem de preferência quando DB_DRIVER não é informado: usa o mais moderno
# instalado e cai para o legado "SQL Server" só se não houver outro.
_PREFERENCIA_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]

_driver_cache: Optional[str] = None


def _resolver_driver() -> str:
    """Driver ODBC a usar: DB_DRIVER do .env, senão o melhor instalado."""
    global _driver_cache
    if _driver_cache is not None:
        return _driver_cache

    forcado = os.getenv("DB_DRIVER")
    if forcado and forcado.strip():
        _driver_cache = forcado.strip()
    else:
        disponiveis = {d for d in pyodbc.drivers()}
        _driver_cache = next(
            (d for d in _PREFERENCIA_DRIVERS if d in disponiveis), "SQL Server"
        )
    log.info("Driver ODBC selecionado: %s", _driver_cache)
    return _driver_cache


class Conexao:
    def __init__(self, ipServidor: str, banco: str, usuario: str, senha: str):
        self._ip = ipServidor
        self._banco = banco
        self._usuario = usuario
        self._senha = senha

    def obter_conexao(self) -> pyodbc.Connection:
        try:
            return pyodbc.connect(
                f"DRIVER={{{_resolver_driver()}}};"
                f"SERVER={self._ip};"
                f"DATABASE={self._banco};"
                f"UID={self._usuario};"
                f"PWD={self._senha};"
                "TrustServerCertificate=YES"
            )
        except pyodbc.Error as e:
            raise ConexaoError(f"Falha ao conectar no banco {self._banco}: {e}") from e


class Executor(Conexao):
    def executar_query(
        self, *, query: str, parametros: Optional[list] = None, fetch: Optional[str] = None
    ) -> Any:
        """Executa uma query.

        fetch="one"  -> dict | None
        fetch="all"  -> list[dict]
        fetch=None   -> executa e faz commit (INSERT/UPDATE/DELETE)
        """
        parametros = parametros or []
        conexao = self.obter_conexao()
        try:
            cursor = conexao.cursor()
            cursor.execute(query, parametros)

            if fetch == "one":
                colunas = [c[0] for c in cursor.description]
                linha = cursor.fetchone()
                return dict(zip(colunas, linha)) if linha else None

            if fetch == "all":
                colunas = [c[0] for c in cursor.description]
                return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]

            conexao.commit()
            return None
        except pyodbc.Error as e:
            conexao.rollback()
            raise ConexaoError(f"Erro ao executar query: {e}") from e
        finally:
            conexao.close()
