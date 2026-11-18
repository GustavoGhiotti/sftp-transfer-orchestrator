# Chaves privadas (.pem) do SFTP

Coloque aqui os arquivos de chave privada usados na autenticação por chave
do SFTP (um por cedente, quando `SENHA` estiver vazia na `TB_CONEXAO_SFTP`).

## Como usar

1. Copie o `.pem` para esta pasta, ex.: `chaves/cedente_77.pem`.
2. Na `TB_CONEXAO_SFTP`, aponte a chave. Há duas formas equivalentes:

   ```sql
   -- (a) no campo proprio
   UPDATE TB_CONEXAO_SFTP
   SET ARQUIVO_CHAVE = 'cedente_77.pem', SENHA = NULL
   WHERE ID_CEDENTE = 77;

   -- (b) atalho: basta pôr o nome do .pem no campo SENHA
   UPDATE TB_CONEXAO_SFTP
   SET SENHA = 'cedente_77.pem'
   WHERE ID_CEDENTE = 77;
   ```

   Se `SENHA` terminar em `.pem`, o robô entende que é ARQUIVO de chave,
   não senha. `ARQUIVO_CHAVE` explícito tem prioridade.

O robô procura o arquivo nesta pasta automaticamente
(`resolver_chave` em `src/config/settings.py`). Também aceita caminho
absoluto em `ARQUIVO_CHAVE`, se preferir guardar fora do robô.
Para mudar a pasta, defina `PASTA_CHAVES` no `.env`.

## Segurança

- **NUNCA** versione as chaves: `.gitignore` já ignora `*.pem` e `*.key`.
- Só este `README.md` fica no repositório.
- Hoje o robô suporta chave **RSA sem passphrase** (ver `sftp_client.py`).
