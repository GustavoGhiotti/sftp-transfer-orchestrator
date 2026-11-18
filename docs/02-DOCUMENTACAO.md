# 02 — Documentação Técnica

> **Fases 3 e 4 do fluxo.** Preencha a Stack na Fase 3 e o restante na Fase 4. A meta é simples:
> um dev novo (ou você daqui a 6 meses) consegue entender, instalar, rodar e usar o projeto
> só lendo este arquivo.

---

## 1. Visão geral

O robô automatiza a coleta de arquivos que os clientes disponibilizam em seus **servidores SFTP**
e os grava em um **destino SMB local** da empresa. Toda a configuração (credenciais do SFTP e o
mapeamento origem→destino de cada arquivo) vive no **banco de dados** — nada é fixado no código.

Um **orquestrador** é disparado pelo Agendador de Tarefas do Windows **a cada 10 minutos**. A cada
disparo ele lê a configuração ativa, descobre quais arquivos ainda **não** foram transferidos
(consultando `TB_TRANSFERENCIAS`), e transfere apenas os pendentes usando um **pool paralelo
limitado**. Cada arquivo transferido é registrado (idempotência) e cada processo gera um log de
execução no banco `LOGS_ROBOS` (SUCESSO / ERRO / SEM_ARQUIVOS).

Esse desenho substitui o modelo antigo (vários `.bat`, um por cliente) por **um único ponto de
controle**, evitando disparos redundantes e reprocessamento de arquivos já baixados no dia.

**O que o projeto NÃO faz:** não transforma nem valida o conteúdo dos arquivos (apenas transfere);
não envia arquivos de volta para o SFTP (fluxo é sempre origem SFTP → destino SMB); não gerencia o
Agendador do Windows (a tarefa agendada é criada manualmente, ver seção 6).

## 2. Stack e dependências

| Camada | Tecnologia | Versão | Por que foi escolhida |
|---|---|---|---|
| Linguagem | Python | 3.12 | Mesma linguagem dos robôs de referência (RoboCargas/RoboArquivosSFTP); equipe domina |
| Framework | — (script/automação) | — | Não precisa de framework; paralelismo com `concurrent.futures` (stdlib) |
| Banco de dados | SQL Server | — | Infra existente (.66); config + banco `LOGS_ROBOS` na mesma instância |
| Biblioteca | `paramiko` | `>=4,<5` | Cliente SFTP com autenticação por senha ou chave `.pem`; já validado no RoboCargas |
| Biblioteca | `smbprotocol` | `>=1.12,<2` | Gravação no destino SMB em stream por chunks, sem `net use` |
| Biblioteca | `pyodbc` | `>=5,<6` | Acesso ao SQL Server (config + logs); padrão da equipe |
| Biblioteca | `python-dotenv` | `>=1,<2` | Carrega segredos do `.env` (fora do código) |
| Biblioteca (dev) | `pytest` | `>=8,<9` | Testes automatizados (Fase 6) |
| Serviço externo | SFTP dos clientes | — | Origem dos arquivos (credenciais em `TB_CONEXAO_SFTP`) |
| Serviço externo | Compartilhamento SMB (.64) | — | Destino local dos arquivos na empresa |
| Serviço externo | Agendador de Tarefas do Windows | — | Dispara `start/run.bat` a cada 10 min |

> Regra: **toda dependência tem uma justificativa**. Versões fixadas em
> [`requirements.txt`](../requirements.txt). Paralelismo e logging usam a biblioteca
> padrão do Python (`concurrent.futures`, `logging`), sem dependência extra.

## 3. Pré-requisitos

- **Python 3.12** (64 bits) instalado na máquina que roda o robô.
- **Microsoft ODBC Driver for SQL Server** (a string de conexão usa `DRIVER=SQL SERVER`).
- **Acesso de rede** ao servidor de banco `.66` (config + `LOGS_ROBOS`) e ao compartilhamento SMB `.64`.
- **Credenciais**: usuário do banco `.66`, usuário do SMB `.64`, e as credenciais dos SFTP dos
  clientes já cadastradas em `TB_CONEXAO_SFTP`.
- **Banco preparado**: as 4 tabelas criadas (rodar `sql/01_criar_tabelas.sql`).

## 4. Instalação

```bash
# 1. Clonar
git clone <repositorio>
cd AutomacaoOrganizacaoArquivos

# 2. Criar e ativar o ambiente virtual (Windows)
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
copy .env.example .env
# edite o .env com os valores reais (banco, SMB, workers)

# 5. Preparar o banco (rodar uma vez, no SQL Server .66)
#    Execute os scripts da pasta sql/ (ver seção 6).

# 6. Rodar manualmente para testar
python -m src.main
```

## 5. Variáveis de ambiente

Ver [`.env.example`](../.env.example). Todas são obrigatórias, exceto onde indicado.

| Variável | Descrição | Obrigatória | Exemplo |
|---|---|---|---|
| `DB_SFTP_SERVER` | Servidor do banco de configuração | Sim | `10.0.0.66` |
| `DB_SFTP_DATABASE` | Banco com as tabelas de config (conexão, mapa, transferências) | Sim | `DB_SFTP` |
| `DB_SFTP_USER` | Usuário do banco de config | Sim | `robo_user` |
| `DB_SFTP_PASSWORD` | Senha do banco de config | Sim | `••••••` |
| `DB_LOGS_SERVER` | Servidor do banco de logs | Sim | `10.0.0.66` |
| `DB_LOGS_DATABASE` | Banco de logs | Sim | `LOGS_ROBOS` |
| `DB_LOGS_USER` | Usuário do banco de logs | Sim | `robo_user` |
| `DB_LOGS_PASSWORD` | Senha do banco de logs | Sim | `••••••` |
| `SMB_SERVER` | Servidor do compartilhamento de destino | Sim | `10.0.0.64` |
| `SMB_USER` | Usuário do SMB | Sim | `svc_robo` |
| `SMB_PASSWORD` | Senha do SMB | Sim | `••••••` |
| `MAX_WORKERS` | Nº de transferências simultâneas (pool) | Não (def. 4) | `4` |
| `CHUNK_MB` | Tamanho do bloco de leitura/gravação (MB) | Não (def. 64) | `64` |

## 6. Como usar

### Rodar manualmente (teste/execução avulsa)

```bash
venv\Scripts\activate
python -m src.main
```

O robô lê a configuração, transfere os arquivos pendentes e encerra. Para acompanhar, veja o log em
arquivo (pasta de logs) e a tabela `LOGS_ROBOS.TB_LOG_EXECUCAO`.

### Preparar o banco (uma vez)

Execute no SQL Server, na ordem, os scripts da pasta `sql/`:

- `sql/01_criar_tabelas.sql` — cria `TB_CONEXAO_SFTP`, `TB_ARQUIVO_MAPA`, `TB_TRANSFERENCIAS`
  (banco de config) e `TB_LOG_EXECUCAO` (banco `LOGS_ROBOS`).

Depois, cadastre 1 linha em `TB_CONEXAO_SFTP` por cliente e 1 linha em `TB_ARQUIVO_MAPA` por
arquivo (origem→destino). Só linhas com `ATIVO = 1` são processadas.

### Agendar a execução a cada 10 minutos (produção)

Criar uma tarefa no **Agendador de Tarefas do Windows** que executa `start\run.bat`:

```powershell
schtasks /Create /TN "RoboTransferenciaSFTP" /TR "C:\Robos\AutomacaoOrganizacaoArquivos\start\run.bat" /SC MINUTE /MO 10 /RL HIGHEST /F
```

> A trava de execução (`file_lock`) garante que, se um ciclo passar de 10 min, o próximo disparo
> não roda em paralelo — ele apenas encerra.

## 7. Estrutura de pastas do projeto

```
AutomacaoOrganizacaoArquivos/
├── docs/                 # documentação do padrão + diagramas
├── sql/                  # scripts DDL das tabelas
├── src/
│   ├── main.py           # entrada chamada pelo agendador
│   ├── config/           # carrega .env (settings)
│   ├── domain/           # entidades + interfaces (contratos)
│   ├── application/       # orquestrador + serviço de transferência
│   ├── infrastructure/   # database, sftp, smb, lock (implementações)
│   └── shared/           # logger, exceptions
├── tests/                # testes automatizados (Fase 6)
├── start/run.bat         # agendador → python -m src.main
├── requirements.txt      # dependências (versões fixadas)
└── .env.example          # modelo das variáveis de ambiente
```

## 8. Como rodar em produção / deploy

Não há build/publicação: o robô roda na própria máquina Windows via Agendador de Tarefas (seção 6).
Deploy = atualizar o código na máquina, `pip install -r requirements.txt` no venv e garantir que a
tarefa agendada aponta para `start\run.bat`.

## 9. Manutenção e contato

- **Responsável:** Equipe de Desenvolvimento (desenvolvimento@empresa.example).
- **SFTP de um cliente fora do ar:** o processo daquele mapa registra `STATUS=ERRO` em
  `TB_LOG_EXECUCAO` e é retentado no próximo ciclo; os demais clientes seguem normalmente.
- **Sem acesso ao SMB:** verificar credenciais `SMB_*` no `.env` e a disponibilidade do `.64`.
- **Robô "não roda":** pode haver lock preso. Conferir/limpar o arquivo de lock (o `file_lock`
  detecta lock morto automaticamente; em último caso, removê-lo manualmente).
- **Arquivo não transferiu:** conferir se o `PADRAO_ARQUIVO` do mapa casa com o nome real e se o
  arquivo já não consta em `TB_TRANSFERENCIAS`.

---

**Critério de pronto (Fase 4):** um dev novo clona, instala e roda o projeto usando apenas
este documento, sem precisar perguntar nada.
