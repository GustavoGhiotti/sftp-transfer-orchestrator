"""Contrato do DESTINO (para onde o robô grava/envia arquivos).

Papel de ESCRITA. Vale para qualquer protocolo (SFTP, SMB, ...): o serviço
de transferência só depende deste contrato, não da tecnologia concreta.
Implementações: infrastructure/smb/smb_client.py e infrastructure/sftp/sftp_client.py.
"""

from typing import Protocol


class IDestino(Protocol):
    def criar_diretorio(self, caminho_arquivo: str) -> None:
        """Garante que a pasta do arquivo de destino existe (cria se faltar)."""
        ...

    def abrir_escrita(self, caminho: str):
        """Handle de escrita binária (context manager) para stream por chunks."""
        ...

    def existe(self, caminho: str) -> bool: ...

    def join_path(self, pasta: str, nome: str) -> str:
        """Junta pasta + nome no separador NATIVO do destino (UNC \\ p/ SMB)."""
        ...

    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def close(self) -> None: ...
