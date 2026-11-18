"""Orquestrador / Controlador — coração do robô.

A cada disparo de 10 min:
  1. Adquire o LOCK de execução (se já houver um rodando, encerra).
  2. Carrega os mapas ANTARES (JOIN por ID_CEDENTE traz credencial + comportamento).
  3. Processa os mapas em POOL paralelo limitado (MAX_WORKERS).
  4. Cada mapa gera 1 log (SUCESSO|ERRO|SEM_ARQUIVOS), agrupados por ID_EXECUCAO.
  5. Libera o LOCK.

Não faz I/O de arquivo direto — delega ao TransferenciaService.
"""

import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from uuid import uuid4

from src.application.transferencia_service import TransferenciaService
from src.config.settings import (
    MAX_WORKERS,
    MODO_TESTE,
    conexao_logs_db,
    conexao_sftp_db,
    credenciais_smb_por_servidor,
    destino_teste,
)
from src.domain.entities.resultado import STATUS_ERRO, ResultadoTransferencia
from src.infrastructure.database.repo_config import RepoConfig
from src.infrastructure.database.repo_logs import RepoLogs
from src.infrastructure.database.repo_transferencias import RepoTransferencias
from src.infrastructure.fabrica_conexao import FabricaConexao, redirecionar_destino
from src.infrastructure.lock.file_lock import ExecucaoLock
from src.shared.logger import get_logger

log = get_logger(__name__)


class Orquestrador:
    def executar(self) -> None:
        with ExecucaoLock() as travou:
            if not travou:
                return
            self._rodar()

    def _rodar(self) -> None:
        id_execucao = str(uuid4())
        maquina = platform.node()
        log.info("Execução %s iniciada (máquina %s)", id_execucao, maquina)

        repo_config = RepoConfig(conexao_sftp_db())
        repo_transferencias = RepoTransferencias(conexao_sftp_db())
        repo_logs = RepoLogs(conexao_logs_db())

        # A fábrica decide, por mapa, se origem/destino é SFTP ou SMB (pelo caminho).
        # A sessão de cada servidor SMB é registrada sob demanda na 1ª vez que for usada.
        fabrica = FabricaConexao(credenciais_smb_por_servidor())

        mapas = repo_config.listar_mapas_ativos()
        if not mapas:
            log.info("Nenhum mapa ativo. Encerrando.")
            return
        log.info("%s mapa(s) ativo(s) na fila.", len(mapas))

        # MODO_TESTE: redireciona só o DESTINO (em memória) para não afetar
        # os caminhos reais nem exigir alteração na tabela. A origem é a real.
        if MODO_TESTE:
            base = destino_teste()
            log.warning("MODO_TESTE ATIVO: destinos redirecionados para %s", base)
            for mapa in mapas:
                mapa["DESTINO"] = redirecionar_destino(mapa["DESTINO"], base)

        service = TransferenciaService(fabrica, repo_transferencias)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futuros = {pool.submit(service.processar_mapa, m): m for m in mapas}
            for futuro in as_completed(futuros):
                mapa = futuros[futuro]
                try:
                    resultado = futuro.result()
                except Exception as exc:  # noqa: BLE001 - rede de segurança
                    log.exception("Falha inesperada no mapa %s", mapa["ID_MAPA"])
                    resultado = ResultadoTransferencia(
                        id_mapa=mapa["ID_MAPA"],
                        id_cedente=mapa["ID_CEDENTE"],
                        nm_cedente=mapa.get("NM_CEDENTE") or "",
                        dt_inicio=datetime.now(),
                        dt_fim=datetime.now(),
                        status=STATUS_ERRO,
                        mensagem=str(exc),
                    )
                self._logar(repo_logs, resultado, id_execucao, maquina)

        log.info("Execução %s finalizada.", id_execucao)

    @staticmethod
    def _logar(
        repo_logs: RepoLogs,
        resultado: ResultadoTransferencia,
        id_execucao: str,
        maquina: str,
    ) -> None:
        try:
            repo_logs.registrar_execucao(
                id_execucao=id_execucao,
                id_mapa=resultado.id_mapa,
                id_cedente=resultado.id_cedente,
                nm_cedente=resultado.nm_cedente,
                dt_inicio=resultado.dt_inicio,
                dt_fim=resultado.dt_fim,
                status=resultado.status,
                qtd_arquivos=resultado.qtd_arquivos,
                nm_arquivos=resultado.nomes_como_texto(),
                mensagem=resultado.mensagem,
                maquina=maquina,
            )
        except Exception:  # noqa: BLE001 - falha ao logar não pode derrubar o robô
            log.exception("Falha ao gravar log do mapa %s", resultado.id_mapa)
