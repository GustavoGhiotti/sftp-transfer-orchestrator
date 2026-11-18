"""Fakes de infraestrutura para os testes (sem SFTP/SMB/banco reais)."""

import io
import ntpath
import posixpath


class _Writer:
    """Handle de escrita fake: captura os bytes ao fechar o contexto."""

    def __init__(self, store: dict, caminho: str):
        self._store = store
        self._caminho = caminho
        self._buf = bytearray()

    def write(self, data: bytes) -> None:
        self._buf += data

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self._store[self._caminho] = bytes(self._buf)


class FakeDestino:
    """Destino fake (papel de escrita). Junta caminho no separador escolhido."""

    def __init__(self, sep: str = "smb"):
        self.arquivos: dict[str, bytes] = {}
        self._join = ntpath.join if sep == "smb" else posixpath.join

    def criar_diretorio(self, caminho: str) -> None:
        pass

    def abrir_escrita(self, caminho: str) -> _Writer:
        return _Writer(self.arquivos, caminho)

    def existe(self, caminho: str) -> bool:
        return caminho in self.arquivos

    def join_path(self, pasta: str, nome: str) -> str:
        return self._join(pasta.rstrip("\\/"), nome)

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def close(self) -> None:
        pass


# Compat: alguns testes ainda referem FakeSMB
FakeSMB = FakeDestino


class FakeOrigem:
    """Origem fake (papel de leitura). `arquivos` indexado pelo nome-base."""

    def __init__(self, listing: list[dict], arquivos: dict[str, bytes], sep: str = "sftp"):
        self.listing = listing
        self.arquivos = arquivos
        self._join = posixpath.join if sep == "sftp" else ntpath.join

    def listar_arquivos_com_info(self, caminho: str) -> list[dict]:
        return self.listing

    def validar_arquivo_pronto(self, caminho: str, *a, **k) -> bool:
        return True

    def abrir_leitura(self, caminho: str):
        base = caminho.replace("\\", "/").split("/")[-1]
        return io.BytesIO(self.arquivos[base])

    def join_path(self, pasta: str, nome: str) -> str:
        return self._join(pasta.rstrip("\\/"), nome)

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def close(self) -> None:
        pass


class FakeFabrica:
    """Fábrica fake: devolve a origem e o destino fakes preparados no teste.

    Se `erro_origem` for setado, criar_origem levanta (simula host fora do ar).
    """

    def __init__(self, origem=None, destino=None, erro_origem: Exception | None = None):
        self.origem = origem
        self.destino = destino if destino is not None else FakeDestino()
        self.erro_origem = erro_origem

    def criar_origem(self, mapa: dict):
        if self.erro_origem is not None:
            raise self.erro_origem
        return self.origem

    def criar_destino(self, mapa: dict):
        return self.destino


class FakeRepoTransferencias:
    def __init__(self, ja_transferidos=None, transferiu_hoje=False):
        self._ja = set(ja_transferidos or [])
        self._hoje = transferiu_hoje
        self.registros: list[dict] = []

    def ja_transferiu_hoje(self, id_mapa: int) -> bool:
        return self._hoje

    def nomes_ja_transferidos(self, id_mapa: int) -> set[str]:
        return set(self._ja)

    def registrar(self, **kwargs) -> None:
        self.registros.append(kwargs)


class FakeRepoLogs:
    def __init__(self):
        self.logs: list[dict] = []

    def registrar_execucao(self, **kwargs) -> None:
        self.logs.append(kwargs)


def make_fake_sftp(listing: list[dict], arquivos: dict[str, bytes]):
    """Compat: devolve uma FÁBRICA fake com origem SFTP-like já montada.

    Mantido para os testes existentes. `arquivos` é indexado pelo nome-base.
    """
    return FakeFabrica(origem=FakeOrigem(listing, arquivos))
