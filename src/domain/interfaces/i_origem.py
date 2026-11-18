"""Contrato da ORIGEM (fonte de onde o robô lê/baixa arquivos).

Papel de LEITURA. Vale para qualquer protocolo (SFTP, SMB, ...): o serviço
de transferência só depende deste contrato, não da tecnologia concreta.
Implementações: infrastructure/sftp/sftp_client.py e infrastructure/smb/smb_client.py.
"""

from typing import Protocol


class IOrigem(Protocol):
    def listar_arquivos_com_info(self, caminho: str) -> list[dict]:
        """Lista arquivos regulares da pasta: [{nome, bytes, mtime, data}]."""
        ...

    def abrir_leitura(self, caminho: str):
        """Handle de leitura binária (context manager) para stream por chunks."""
        ...

    def validar_arquivo_pronto(self, caminho: str) -> bool:
        """True se o arquivo não está mais em upload (tamanho estável)."""
        ...

    def join_path(self, pasta: str, nome: str) -> str:
        """Junta pasta + nome no separador NATIVO da origem (posix p/ SFTP)."""
        ...

    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def close(self) -> None: ...
