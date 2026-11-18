# RoboTransferenciaSFTP

> **Versão de portfólio.** Código real de produção, anonimizado: nomes de empresa, clientes, pessoas, hosts, e-mails e credenciais foram trocados por valores fictícios (`Acme`, `Banco Alfa`, `10.0.0.x`, `empresa.example`). Toda configuração sensível vem do `.env` (modelo em `.env.example`). O código não aponta para nenhum sistema real.

Robô que, **a cada 10 minutos**, baixa arquivos do **SFTP de cada cliente** e os grava em um
**destino SMB local** da empresa. Toda a configuração (credenciais e mapa origem→destino) fica no
banco de dados; um **orquestrador** decide o que rodar, transfere só o que ainda não foi transferido
(idempotente) e registra cada execução em log.

> Projeto no padrão **Grupo Acme**. Antes de mexer, leia o [`PROJETO.md`](PROJETO.md) e os
> documentos em [`docs/`](docs/). **Status atual: Fase 4 (Documentação).**

## Como funciona (resumo)

```
Agendador (10 min) → Orquestrador → [lê config no banco] → transfere pendentes (pool paralelo)
                                   → registra transferência + grava log (SUCESSO/ERRO/SEM_ARQUIVOS)
```

Detalhes e diagramas em [`docs/01-ARQUITETURA.md`](docs/01-ARQUITETURA.md).

## Rodar em 4 passos

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # e preencha os valores reais
```

Preparar o banco (uma vez): rodar [`sql/01_criar_tabelas.sql`](sql/01_criar_tabelas.sql) no
SQL Server `.66`. Depois, executar:

```bash
python -m src.main
```

Guia completo (pré-requisitos, variáveis, agendamento, troubleshooting) em
[`docs/02-DOCUMENTACAO.md`](docs/02-DOCUMENTACAO.md).

## Estrutura

```
src/
├── main.py            # entrada chamada pelo agendador
├── config/            # carrega .env
├── domain/            # entidades + interfaces (contratos)
├── application/       # orquestrador + serviço de transferência
├── infrastructure/    # database, sftp, smb, lock
└── shared/            # logger, exceptions
```

## Stack

Python 3.12 · `paramiko` (SFTP) · `smbprotocol` (SMB) · `pyodbc` (SQL Server) · `python-dotenv` ·
`pytest`. Pool e logging via stdlib. Versões em [`requirements.txt`](requirements.txt).
