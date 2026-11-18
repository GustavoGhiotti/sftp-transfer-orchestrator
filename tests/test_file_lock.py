"""Testes da trava de execução (evita sobreposição; detecta lock morto)."""

from datetime import datetime, timedelta

from src.infrastructure.lock.file_lock import ExecucaoLock


def test_adquire_e_libera(tmp_path):
    caminho = tmp_path / "robo.lock"
    lock = ExecucaoLock(caminho=caminho)
    assert lock.adquirir() is True
    assert caminho.exists()
    lock.liberar()
    assert not caminho.exists()


def test_segunda_execucao_e_bloqueada(tmp_path):
    caminho = tmp_path / "robo.lock"
    lock1 = ExecucaoLock(caminho=caminho)
    assert lock1.adquirir() is True

    lock2 = ExecucaoLock(caminho=caminho)
    assert lock2.adquirir() is False  # já há execução em andamento

    lock1.liberar()
    assert lock2.adquirir() is True  # liberado, agora entra


def test_lock_morto_por_idade_e_assumido(tmp_path):
    caminho = tmp_path / "robo.lock"
    velho = (datetime.now() - timedelta(minutes=45)).isoformat()
    caminho.write_text(f"99999|{velho}", encoding="utf-8")

    lock = ExecucaoLock(caminho=caminho, tempo_max=timedelta(minutes=30))
    assert lock.adquirir() is True  # lock antigo considerado morto


def test_lock_ilegivel_e_assumido(tmp_path):
    caminho = tmp_path / "robo.lock"
    caminho.write_text("conteudo-invalido-sem-pipe", encoding="utf-8")

    lock = ExecucaoLock(caminho=caminho)
    assert lock.adquirir() is True
