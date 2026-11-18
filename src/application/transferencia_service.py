"""TransferenciaService — executa UM mapa (origem -> destino).

Genérico quanto ao protocolo: a FÁBRICA decide se origem e destino são SFTP
ou SMB (colunas TIPO_ORIGEM / TIPO_DESTINO). O serviço só fala com os papéis
IOrigem (lê/lista) e IDestino (grava), então funciona em qualquer sentido:
SFTP->SMB, SMB->SFTP, SMB->SMB, SFTP->SFTP.

Etapas (o QUE varia vem das colunas do mapa; o resto é regra fixa):

  1. Lista a origem (ORIGEM) e filtra por PADRAO_ARQUIVO
     (e por data do arquivo, se SOMENTE_HOJE).
  2. Remove os que já estão em TB_TRANSFERENCIAS (idempotência).
  3. Para cada arquivo novo (valida que está pronto antes de baixar):
       - se for .zip: extrai e grava APENAS o conteúdo (arquivo interno de
         mesmo nome, outra extensão); o .zip não é salvo  -> REGRA FIXA;
       - senão: grava o arquivo direto no DESTINO (stream por chunks);
       - se RENOMEAR_COM_DATA: acrescenta _AAAAMMDD ao nome final.
  4. Registra a transferência (TB_TRANSFERENCIAS, pelo nome de ORIGEM) e
     devolve um ResultadoTransferencia para o orquestrador logar.

Erro em um arquivo não derruba os demais nem registra a transferência
(o arquivo será retentado no próximo ciclo). O método nunca levanta exceção:
falhas viram STATUS=ERRO no resultado.
"""

import fnmatch
import io
import ntpath
import re
import zipfile
from datetime import date, datetime
from pathlib import Path

from src.config.settings import CHUNK_MB, ESPERA_ARQUIVO_SEG, TENTATIVAS_ARQUIVO
from src.domain.entities.resultado import (
    STATUS_ERRO,
    STATUS_SEM_ARQUIVOS,
    STATUS_SUCESSO,
    ResultadoTransferencia,
)
from src.domain.interfaces.i_destino import IDestino
from src.domain.interfaces.i_origem import IOrigem
from src.infrastructure.database.repo_transferencias import RepoTransferencias
from src.infrastructure.fabrica_conexao import FabricaConexao
from src.shared.logger import get_logger

log = get_logger(__name__)

_RUN_DIGITOS = re.compile(r"\d+")


def derivar_padrao(exemplo: str) -> str:
    """Deriva um glob a partir do NOME DE UM ARQUIVO REAL, trocando cada
    sequência de números por curinga (as partes que variam: data, hora, seq).

    Ex.: '20260521_ACORDO_ATUAL_0757_OUT.csv' -> '*_ACORDO_ATUAL_*_OUT.csv'
    Assim o operador cadastra só um exemplo do arquivo que chega, sem montar
    o padrão à mão.
    """
    padrao = _RUN_DIGITOS.sub("*", exemplo)
    return re.sub(r"\*+", "*", padrao)  # colapsa curingas adjacentes


class TransferenciaService:
    def __init__(self, fabrica: FabricaConexao, repo_transferencias: RepoTransferencias):
        self.fabrica = fabrica
        self.repo = repo_transferencias
        self.chunk = CHUNK_MB * 1024 * 1024

    def processar_mapa(self, mapa: dict) -> ResultadoTransferencia:
        resultado = ResultadoTransferencia(
            id_mapa=mapa["ID_MAPA"],
            id_cedente=mapa["ID_CEDENTE"],
            nm_cedente=mapa.get("NM_CEDENTE") or "",
            dt_inicio=datetime.now(),
        )
        try:
            self._executar(mapa, resultado)
        except Exception as exc:  # noqa: BLE001 - mapa não pode derrubar os outros
            log.exception("Erro no mapa %s (cedente %s)", mapa["ID_MAPA"], mapa["ID_CEDENTE"])
            resultado.status = STATUS_ERRO
            resultado.mensagem = str(exc)
        finally:
            resultado.dt_fim = datetime.now()
        return resultado

    # ------------------------------------------------------------------
    def _executar(self, mapa: dict, resultado: ResultadoTransferencia) -> None:
        origem_dir = mapa["ORIGEM"]
        destino_dir = mapa["DESTINO"]
        somente_hoje = bool(mapa.get("SOMENTE_HOJE"))
        renomear = bool(mapa.get("RENOMEAR_COM_DATA"))

        # Atalho do agendador: se o mapa só quer o arquivo do dia e ele JÁ foi
        # transferido hoje, nem conecta na origem (evita N conexões inúteis).
        if somente_hoje and self.repo.ja_transferiu_hoje(mapa["ID_MAPA"]):
            resultado.status = STATUS_SEM_ARQUIVOS
            return

        ja_transferidos = self.repo.nomes_ja_transferidos(mapa["ID_MAPA"])
        erros: list[str] = []

        with self.fabrica.criar_origem(mapa) as origem, self.fabrica.criar_destino(mapa) as destino:
            candidatos = self._filtrar(
                origem.listar_arquivos_com_info(origem_dir),
                padrao=mapa["PADRAO_ARQUIVO"],
                somente_hoje=somente_hoje,
                ja_transferidos=ja_transferidos,  # trava: já transferidos saem da lista (silencioso)
            )

            if not candidatos:
                resultado.status = STATUS_SEM_ARQUIVOS
                return

            log.info(
                "Mapa %s (cedente %s): %s arquivo(s) a transferir.",
                mapa["ID_MAPA"], mapa["ID_CEDENTE"], len(candidatos),
            )

            for indice, info in enumerate(candidatos, start=1):
                nome = info["nome"]
                caminho_origem = origem.join_path(origem_dir, nome)
                try:
                    log.info(
                        "[%s/%s] Verificando %s (%s bytes)...",
                        indice, len(candidatos), nome, info.get("bytes"),
                    )
                    if not origem.validar_arquivo_pronto(
                        caminho_origem,
                        tentativas=TENTATIVAS_ARQUIVO,
                        espera=ESPERA_ARQUIVO_SEG,
                    ):
                        log.info("Arquivo %s ainda em cópia; será retentado.", nome)
                        continue

                    log.info("[%s/%s] Transferindo %s...", indice, len(candidatos), nome)
                    if nome.lower().endswith(".zip"):
                        gravados = self._transferir_zip(
                            origem, destino, caminho_origem, destino_dir, renomear
                        )
                    else:
                        gravados = self._transferir_simples(
                            origem, destino, caminho_origem, nome, destino_dir, renomear
                        )

                    self.repo.registrar(
                        id_mapa=mapa["ID_MAPA"],
                        id_cedente=mapa["ID_CEDENTE"],
                        nm_arquivo=nome,  # nome de ORIGEM (idempotência sobre a fonte)
                        dt_arquivo=info["data"],
                        tamanho_bytes=info["bytes"],
                    )
                    resultado.nm_arquivos.extend(gravados)
                    resultado.qtd_arquivos += len(gravados)
                except Exception as exc:  # noqa: BLE001 - um arquivo não derruba o mapa
                    log.exception("Falha no arquivo %s", nome)
                    erros.append(f"{nome}: {exc}")

        if resultado.qtd_arquivos > 0:
            resultado.status = STATUS_SUCESSO
            if erros:
                resultado.mensagem = "Parcial. Falhas: " + " | ".join(erros)
        elif erros:
            resultado.status = STATUS_ERRO
            resultado.mensagem = " | ".join(erros)
        else:
            resultado.status = STATUS_SEM_ARQUIVOS

    # ------------------------------------------------------------------
    def _filtrar(
        self, arquivos: list[dict], *, padrao: str, somente_hoje: bool, ja_transferidos: set
    ) -> list[dict]:
        hoje = date.today()
        selecionados = []
        for info in arquivos:
            if not self._casa_padrao(info["nome"], padrao):
                continue
            if somente_hoje and info["data"] != hoje:
                continue
            if info["nome"] in ja_transferidos:
                continue
            selecionados.append(info)
        return selecionados

    @staticmethod
    def _casa_padrao(nome: str, padrao: str) -> bool:
        """Casa o arquivo com o valor de PADRAO_ARQUIVO, que pode ser:
        - glob explícito ('*.zip', 'remessa_*.csv') -> usa como está;
        - NOME de exemplo com números ('2026..._OUT.csv') -> deriva o padrão;
        - extensão/sufixo sem números ('.ret') -> casa pelo final do nome.
        """
        n, p = nome.lower(), padrao.lower()
        if any(ch in p for ch in "*?[]"):
            return fnmatch.fnmatch(n, p)  # glob explícito
        if any(ch.isdigit() for ch in p):
            return fnmatch.fnmatch(n, derivar_padrao(p))  # exemplo de nome real
        return n.endswith(p)  # extensão/sufixo

    @staticmethod
    def _nome_final(nome: str, renomear: bool) -> str:
        if not renomear:
            return nome
        p = Path(nome)
        return f"{p.stem}_{date.today().strftime('%Y%m%d')}{p.suffix}"

    def _transferir_simples(
        self,
        origem: IOrigem,
        destino: IDestino,
        caminho_origem: str,
        nome: str,
        destino_dir: str,
        renomear: bool,
    ) -> list[str]:
        nome_final = self._nome_final(nome, renomear)
        caminho_destino = destino.join_path(destino_dir, nome_final)
        destino.criar_diretorio(caminho_destino)
        with origem.abrir_leitura(caminho_origem) as origem_f, destino.abrir_escrita(
            caminho_destino
        ) as destino_f:
            while True:
                bloco = origem_f.read(self.chunk)
                if not bloco:
                    break
                destino_f.write(bloco)
        log.info("Transferido: %s -> %s", nome, caminho_destino)
        return [nome_final]

    def _transferir_zip(
        self,
        origem: IOrigem,
        destino: IDestino,
        caminho_origem: str,
        destino_dir: str,
        renomear: bool,
    ) -> list[str]:
        """Extrai e grava só o conteúdo do .zip (o .zip não é salvo)."""
        with origem.abrir_leitura(caminho_origem) as origem_f:
            dados = io.BytesIO(origem_f.read())

        gravados: list[str] = []
        with zipfile.ZipFile(dados) as zf:
            for interno in zf.infolist():
                if interno.is_dir():
                    continue
                nome_interno = ntpath.basename(interno.filename)
                nome_final = self._nome_final(nome_interno, renomear)
                caminho_destino = destino.join_path(destino_dir, nome_final)
                destino.criar_diretorio(caminho_destino)
                with zf.open(interno) as conteudo, destino.abrir_escrita(caminho_destino) as destino_f:
                    while True:
                        bloco = conteudo.read(self.chunk)
                        if not bloco:
                            break
                        destino_f.write(bloco)
                log.info("Extraído de zip: %s -> %s", nome_interno, caminho_destino)
                gravados.append(nome_final)
        return gravados
