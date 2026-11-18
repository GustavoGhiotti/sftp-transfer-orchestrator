"""Exceções próprias do robô."""


class RoboError(Exception):
    """Base de todas as exceções do robô."""


class ConfiguracaoInvalida(RoboError):
    """Faltou variável de ambiente ou configuração inválida."""


class ConexaoError(RoboError):
    """Falha de conexão (SFTP, SMB ou banco) após as tentativas."""


class TransferenciaError(RoboError):
    """Falha ao transferir/processar um arquivo."""
