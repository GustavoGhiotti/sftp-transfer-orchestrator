"""Trava de execução — evita sobreposição dos disparos de 10 min.

Escreve um arquivo de lock (PID + timestamp) ao iniciar e o remove ao final.
Se já houver um lock válido, a execução atual não roda. Um lock "morto"
(mais velho que o tempo máximo esperado de execução) é considerado inválido
e substituído, para o robô nunca travar para sempre.

Uso:
    with ExecucaoLock() as travou:
        if not travou:
            return   # já existe uma execução em andamento
        ...  # trabalho protegido
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from src.shared.logger import get_logger

log = get_logger(__name__)

_ARQUIVO_LOCK = Path(__file__).resolve().parents[3] / "robo.lock"
# Uma execução nunca deveria durar mais que isto; passou disso, o lock é dado como morto.
_TEMPO_MAX = timedelta(minutes=30)


class ExecucaoLock:
    def __init__(self, caminho: Path = _ARQUIVO_LOCK, tempo_max: timedelta = _TEMPO_MAX):
        self._caminho = caminho
        self._tempo_max = tempo_max
        self._dono = False

    def adquirir(self) -> bool:
        if self._caminho.exists() and not self._lock_morto():
            log.warning("Já existe uma execução em andamento (lock ativo). Encerrando.")
            return False

        self._caminho.write_text(
            f"{os.getpid()}|{datetime.now().isoformat()}", encoding="utf-8"
        )
        self._dono = True
        return True

    def _lock_morto(self) -> bool:
        try:
            conteudo = self._caminho.read_text(encoding="utf-8").strip()
            _, ts = conteudo.split("|", 1)
            idade = datetime.now() - datetime.fromisoformat(ts)
            if idade > self._tempo_max:
                log.warning("Lock antigo (%s) considerado morto; assumindo.", idade)
                return True
            return False
        except Exception:  # noqa: BLE001 - lock corrompido/ilegível: tratar como morto
            log.warning("Lock ilegível; considerando morto.")
            return True

    def liberar(self) -> None:
        if self._dono and self._caminho.exists():
            try:
                self._caminho.unlink()
            except OSError:
                pass
            self._dono = False

    def __enter__(self) -> bool:
        return self.adquirir()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.liberar()
