"""Testes das regras puras de filtragem/nomeação do TransferenciaService."""

from datetime import date, datetime, timedelta

from src.application.transferencia_service import TransferenciaService, derivar_padrao


def _svc():
    return TransferenciaService(fabrica=None, repo_transferencias=None)


# ---- _casa_padrao -----------------------------------------------------
def test_casa_padrao_curinga_zip():
    assert _svc()._casa_padrao("ARQUIVO.ZIP", "*.zip") is True
    assert _svc()._casa_padrao("arquivo.csv", "*.zip") is False


def test_casa_padrao_extensao_sem_curinga():
    assert _svc()._casa_padrao("retorno.ret", ".ret") is True
    assert _svc()._casa_padrao("retorno.txt", ".ret") is False


def test_casa_padrao_prefixo():
    assert _svc()._casa_padrao("remessa_01.csv", "remessa_*.csv") is True
    assert _svc()._casa_padrao("outro_01.csv", "remessa_*.csv") is False


def test_derivar_padrao_troca_numeros_por_curinga():
    assert (
        derivar_padrao("20260521_ACORDO_ATUAL_0757_OUT.csv")
        == "*_ACORDO_ATUAL_*_OUT.csv"
    )


def test_casa_padrao_por_nome_de_exemplo():
    # cadastrando o NOME de um arquivo real, o robô deriva o padrão sozinho
    exemplo = "20260521_ACORDO_ATUAL_0757_OUT.csv"
    # mesmo layout, outra data e outro horário -> casa
    assert _svc()._casa_padrao("20260522_ACORDO_ATUAL_1830_OUT.csv", exemplo) is True
    # outro tipo (INS no lugar de OUT) -> não casa
    assert _svc()._casa_padrao("20260522_ACORDO_ATUAL_1830_INS.csv", exemplo) is False
    # extensão diferente -> não casa
    assert _svc()._casa_padrao("20260522_ACORDO_ATUAL_1830_OUT.txt", exemplo) is False


# ---- _nome_final ------------------------------------------------------
def test_nome_final_sem_renomear():
    assert _svc()._nome_final("dados.csv", renomear=False) == "dados.csv"


def test_nome_final_com_data():
    hoje = date.today().strftime("%Y%m%d")
    assert _svc()._nome_final("dados.csv", renomear=True) == f"dados_{hoje}.csv"


# ---- _filtrar ---------------------------------------------------------
def _info(nome, dia):
    return {"nome": nome, "bytes": 10, "mtime": datetime.now(), "data": dia}


def test_filtrar_padrao_data_e_ja_transferidos():
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    arquivos = [
        _info("a.zip", hoje),        # ok
        _info("b.csv", hoje),        # padrão não bate
        _info("c.zip", ontem),       # fora do dia
        _info("d.zip", hoje),        # já transferido
    ]
    selecionados = _svc()._filtrar(
        arquivos, padrao="*.zip", somente_hoje=True, ja_transferidos={"d.zip"}
    )
    assert [i["nome"] for i in selecionados] == ["a.zip"]


def test_filtrar_sem_somente_hoje_pega_datas_antigas():
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    arquivos = [_info("a.zip", ontem), _info("b.zip", hoje)]
    selecionados = _svc()._filtrar(
        arquivos, padrao="*.zip", somente_hoje=False, ja_transferidos=set()
    )
    assert {i["nome"] for i in selecionados} == {"a.zip", "b.zip"}


def test_filtrar_vazio():
    assert _svc()._filtrar([], padrao="*.zip", somente_hoje=True, ja_transferidos=set()) == []
