"""Testes da resolução do caminho da chave .pem (resolver_chave)."""

import ntpath
from pathlib import Path

from src.config import settings
from src.config.settings import PASTA_CHAVES, resolver_chave
from src.infrastructure.fabrica_conexao import resolver_credenciais_sftp


def test_vazio_vira_none():
    assert resolver_chave(None) is None
    assert resolver_chave("") is None
    assert resolver_chave("   ") is None


def test_nome_simples_resolve_na_pasta_chaves():
    resolvido = resolver_chave("cedente_77.pem")
    assert resolvido == str(PASTA_CHAVES / "cedente_77.pem")
    # a pasta padrão fica DENTRO do robô
    assert Path(resolvido).parent.name == "chaves"


def test_caminho_absoluto_e_mantido():
    absoluto = r"C:\outra\pasta\chave.pem"
    assert resolver_chave(absoluto) == absoluto


def test_pasta_padrao_e_a_do_projeto():
    # PASTA_CHAVES = <raiz>/chaves, e a raiz contém a pasta src/
    raiz = PASTA_CHAVES.parent
    assert (raiz / "src").is_dir()


# ---- resolver_credenciais_sftp ---------------------------------------
def test_senha_normal_fica_como_senha():
    password, key = resolver_credenciais_sftp("minha_senha", None)
    assert password == "minha_senha"
    assert key is None


def test_senha_com_pem_vira_chave():
    # SENHA terminando em .pem é tratada como arquivo de chave
    password, key = resolver_credenciais_sftp("cedente_81.pem", None)
    assert password is None
    assert key == str(PASTA_CHAVES / "cedente_81.pem")


def test_arquivo_chave_tem_prioridade_sobre_senha():
    password, key = resolver_credenciais_sftp("qualquer.pem", "oficial.pem")
    assert password == "qualquer.pem"  # não vira chave, pois ARQUIVO_CHAVE já veio
    assert key == str(PASTA_CHAVES / "oficial.pem")
