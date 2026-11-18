"""Testes do TransferenciaService com fakes: regra do .zip, rename, erro
isolado e os dois sentidos (SFTP->SMB e SMB->SFTP)."""

import io
import ntpath
import posixpath
import zipfile
from datetime import date, datetime

import pytest

from src.application.transferencia_service import TransferenciaService
from src.domain.entities.resultado import STATUS_ERRO, STATUS_SUCESSO
from src.infrastructure.fabrica_conexao import (
    TIPO_SFTP,
    TIPO_SMB,
    detectar_tipo,
    extrair_servidor_smb,
    redirecionar_destino,
)
from tests.fakes import (
    FakeDestino,
    FakeFabrica,
    FakeOrigem,
    FakeRepoTransferencias,
)


def _mapa(**over):
    base = {
        "ID_MAPA": 1,
        "ID_CEDENTE": 77,
        "NM_CEDENTE": "CLIENTE X",
        "ORIGEM": "/saida",
        "DESTINO": r"\\srv\dest",
        "PADRAO_ARQUIVO": "*.zip",
        "SOMENTE_HOJE": 1,
        "RENOMEAR_COM_DATA": 0,
        "HOSTNAME": "host",
        "USUARIO": "user",
        "PORTA_HOST": 22,
        "SENHA": "senha",
        "ARQUIVO_CHAVE": None,
    }
    base.update(over)
    return base


def _info(nome):
    return {"nome": nome, "bytes": 5, "mtime": datetime.now(), "data": date.today()}


def _zip_bytes(nome_interno: str, conteudo: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(nome_interno, conteudo)
    return buf.getvalue()


@pytest.mark.parametrize(
    "caminho, esperado",
    [
        (r"\\10.0.0.64\arquivos\entrada", TIPO_SMB),
        (r"\\srv\share", TIPO_SMB),
        ("/saida", TIPO_SFTP),
        ("pasta/sub", TIPO_SFTP),
        ("  \\\\srv\\x  ", TIPO_SMB),  # espaços ao redor não atrapalham
    ],
)
def test_detectar_tipo_pelo_caminho(caminho, esperado):
    assert detectar_tipo(caminho) == esperado


@pytest.mark.parametrize(
    "caminho, servidor",
    [
        (r"\\10.0.0.64\arquivos\entrada", "10.0.0.64"),
        (r"\\10.0.0.71\envio", "10.0.0.71"),
        (r"  \\10.0.0.72\a\b  ", "10.0.0.72"),
    ],
)
def test_extrair_servidor_smb(caminho, servidor):
    assert extrair_servidor_smb(caminho) == servidor


def test_redirecionar_destino_smb_preserva_estrutura():
    real = r"\\10.0.0.64\arquivos\entrada"
    base = r"\\10.0.0.72\teste"
    assert redirecionar_destino(real, base) == r"\\10.0.0.72\teste\10.0.0.64\arquivos\entrada"


def test_redirecionar_destino_de_sftp_para_base_smb():
    # origem/destino real SFTP ('/entrada') redirecionado p/ base SMB de teste
    assert redirecionar_destino("/entrada/sub", r"\\srv\teste") == r"\\srv\teste\entrada\sub"


def test_zip_extrai_somente_conteudo():
    conteudo = b"col1;col2\n1;2\n"
    origem = FakeOrigem(
        listing=[_info("dados.zip")],
        arquivos={"dados.zip": _zip_bytes("dados.csv", conteudo)},
    )
    destino = FakeDestino(sep="smb")
    fabrica = FakeFabrica(origem=origem, destino=destino)
    repo = FakeRepoTransferencias()

    resultado = TransferenciaService(fabrica, repo).processar_mapa(_mapa())

    assert resultado.status == STATUS_SUCESSO
    assert resultado.qtd_arquivos == 1
    # gravou o CONTEÚDO (dados.csv), não o zip
    caminho = ntpath.join(r"\\srv\dest", "dados.csv")
    assert destino.arquivos[caminho] == conteudo
    assert all(not k.endswith(".zip") for k in destino.arquivos)
    # idempotência registrada pelo nome de ORIGEM (o zip)
    assert repo.registros[0]["nm_arquivo"] == "dados.zip"


def test_arquivo_simples_com_rename_data():
    origem = FakeOrigem(
        listing=[_info("retorno.ret")],
        arquivos={"retorno.ret": b"conteudo-ret"},
    )
    destino = FakeDestino(sep="smb")
    fabrica = FakeFabrica(origem=origem, destino=destino)
    repo = FakeRepoTransferencias()

    mapa = _mapa(PADRAO_ARQUIVO=".ret", RENOMEAR_COM_DATA=1)
    resultado = TransferenciaService(fabrica, repo).processar_mapa(mapa)

    hoje = date.today().strftime("%Y%m%d")
    caminho = ntpath.join(r"\\srv\dest", f"retorno_{hoje}.ret")
    assert resultado.status == STATUS_SUCESSO
    assert destino.arquivos[caminho] == b"conteudo-ret"


def test_sentido_smb_para_sftp():
    """Origem SMB, destino SFTP: caminho final montado com separador posix."""
    origem = FakeOrigem(
        listing=[_info("remessa.txt")],
        arquivos={"remessa.txt": b"abc"},
        sep="smb",
    )
    destino = FakeDestino(sep="sftp")
    fabrica = FakeFabrica(origem=origem, destino=destino)
    repo = FakeRepoTransferencias()

    mapa = _mapa(
        ORIGEM=r"\\srv\saida",
        DESTINO="/entrada",
        PADRAO_ARQUIVO=".txt",
    )
    resultado = TransferenciaService(fabrica, repo).processar_mapa(mapa)

    caminho = posixpath.join("/entrada", "remessa.txt")
    assert resultado.status == STATUS_SUCESSO
    assert destino.arquivos[caminho] == b"abc"


def test_ja_transferido_nao_reprocessa():
    origem = FakeOrigem(
        listing=[_info("dados.zip")],
        arquivos={"dados.zip": _zip_bytes("dados.csv", b"x")},
    )
    destino = FakeDestino(sep="smb")
    fabrica = FakeFabrica(origem=origem, destino=destino)
    repo = FakeRepoTransferencias(ja_transferidos={"dados.zip"})

    resultado = TransferenciaService(fabrica, repo).processar_mapa(_mapa())

    assert resultado.status == "SEM_ARQUIVOS"
    assert destino.arquivos == {}
    assert repo.registros == []


def test_pula_sem_conectar_se_ja_transferiu_hoje():
    # Se já transferiu hoje, nem tenta criar a conexão de origem.
    fabrica = FakeFabrica(erro_origem=AssertionError("NÃO deveria conectar"))
    repo = FakeRepoTransferencias(transferiu_hoje=True)
    resultado = TransferenciaService(fabrica, repo).processar_mapa(_mapa())
    assert resultado.status == "SEM_ARQUIVOS"
    assert repo.registros == []


def test_erro_na_origem_nao_levanta_e_marca_erro():
    fabrica = FakeFabrica(erro_origem=ConnectionError("host inacessível"))
    resultado = TransferenciaService(fabrica, FakeRepoTransferencias()).processar_mapa(_mapa())

    assert resultado.status == STATUS_ERRO
    assert resultado.mensagem  # mensagem preenchida
    assert resultado.dt_fim is not None
