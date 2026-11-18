/* =====================================================================
   01_criar_tabelas.sql
   Cria as tabelas do robo de transferencia SFTP -> SMB.

   Bancos (servidor .66):
     - DB_SFTP    : TB_CONEXAO_SFTP, TB_ARQUIVO_MAPA, TB_TRANSFERENCIAS
     - LOGS_ROBOS  : TB_LOG_EXECUCAO

   Conceito: o comportamento de cada arquivo e CONFIGURACAO, nao codigo.
   Uma linha em TB_ARQUIVO_MAPA descreve tudo (origem, destino, se
   descompacta, se renomeia, etc). Adicionar um "processo novo" = inserir
   uma linha, sem escrever codigo.

   Vinculo: TB_ARQUIVO_MAPA.ID_CEDENTE  ->  TB_CONEXAO_SFTP.ID_CEDENTE
   ===================================================================== */


/* =====================================================================
   PARTE 1 — Banco DB_SFTP (configuracao operacional do robo)
   ===================================================================== */
USE [DB_SFTP]
GO
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/* ---------------------------------------------------------------------
   Credenciais do SFTP (1 linha por cedente/cliente).
   Segue o padrao legado (Carga.TB_CONEXAO_SFTP): ID_CEDENTE e a CHAVE
   PRINCIPAL usada para casar com TB_ARQUIVO_MAPA.
   --------------------------------------------------------------------- */
IF OBJECT_ID('dbo.TB_CONEXAO_SFTP', 'U') IS NULL
CREATE TABLE [dbo].[TB_CONEXAO_SFTP](
    [ID]             BIGINT IDENTITY(1,1) NOT NULL,   -- surrogate (mantido do legado)
    [ID_CEDENTE]     INT           NOT NULL,          -- CHAVE PRINCIPAL (vinculo com o mapa)
    [NM_CEDENTE]     VARCHAR(255)  NOT NULL,
    [HOSTNAME]       VARCHAR(255)  NULL,
    [USUARIO]        VARCHAR(255)  NULL,
    [SENHA]          VARCHAR(255)  NULL,              -- senha OU nome de um .pem (vira chave)
    [ARQUIVO_CHAVE]  VARCHAR(500)  NULL,              -- nome do .pem na pasta chaves/ (ou caminho absoluto)
    [PORTA_HOST]     INT           NULL,
    [TIPO_PROTOCOLO] VARCHAR(255)  NULL,              -- SFTP | FTP | FTPS
    [PREFIXO_FINAL]  VARCHAR(255)  NULL,
    [ATIVO]          BIT           NOT NULL DEFAULT 1,
    [OBSERVACAO]     VARCHAR(MAX)  NULL,
    [DT_CRIACAO]     DATETIME      NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_TB_CONEXAO_SFTP PRIMARY KEY ([ID_CEDENTE]),
    CONSTRAINT UQ_TB_CONEXAO_ID   UNIQUE ([ID])
)
GO

/* ---------------------------------------------------------------------
   Mapa origem -> destino, 1 linha por ARQUIVO (UNIDADE DE CONTROLE).
   Casa com a credencial por ID_CEDENTE. As colunas de COMPORTAMENTO
   abaixo dizem o que o robo faz com o arquivo — sem codigo por processo.

   GENERICO NO SENTIDO: o PROTOCOLO e detectado pelo formato do caminho,
   sem coluna de tipo:
     - SMB  -> caminho UNC, comeca com '\\' (ex.: \\10.0.0.64\arquivos\...);
     - SFTP -> qualquer outro (ex.: /saida, pasta/sub).
   Assim o mesmo robo faz SFTP->SMB, SMB->SFTP, SMB->SMB. Credencial:
     - lado SFTP usa a credencial do CEDENTE (TB_CONEXAO_SFTP);
     - lado SMB usa o file server interno (credenciais globais do .env).
   --------------------------------------------------------------------- */
IF OBJECT_ID('dbo.TB_ARQUIVO_MAPA', 'U') IS NULL
CREATE TABLE [dbo].[TB_ARQUIVO_MAPA](
    [ID]                 BIGINT IDENTITY(1,1) NOT NULL,
    [ID_CEDENTE]         INT           NOT NULL,      -- FK -> TB_CONEXAO_SFTP(ID_CEDENTE)
    [DESCRICAO]          VARCHAR(255)  NULL,
    [ORIGEM]             VARCHAR(MAX)  NOT NULL,       -- de onde ler  (/remota p/ SFTP, \\srv\share\... p/ SMB)
    [DESTINO]            VARCHAR(MAX)  NOT NULL,       -- para onde gravar (\\10.0.0.64\... p/ SMB, /remota p/ SFTP)
    [PADRAO_ARQUIVO]     VARCHAR(255)  NOT NULL,       -- glob (*.zip) | .ret | ou o NOME de um arquivo real
                                                       --   (ex.: 20260521_ACORDO_ATUAL_0757_OUT.csv);
                                                       --   nesse caso o robo troca os numeros por curinga.
    [SOMENTE_HOJE]       BIT           NOT NULL DEFAULT 1,   -- filtra pela data do arquivo (mtime)
    /* ---- comportamento ----
       Regra IMPLICITA (nao vira coluna): se o arquivo baixado for .zip, o robo
       SEMPRE extrai e grava apenas o CONTEUDO (1 arquivo interno, mesmo nome com
       outra extensao). O .zip em si nao e salvo. */
    [RENOMEAR_COM_DATA]  BIT           NOT NULL DEFAULT 0,   -- unica alteracao no nome: acrescenta _AAAAMMDD
    [ATIVO]              BIT           NOT NULL DEFAULT 1,
    [OBSERVACAO]         VARCHAR(MAX)  NULL,
    [DT_CRIACAO]         DATETIME      NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_TB_ARQUIVO_MAPA PRIMARY KEY ([ID]),
    CONSTRAINT FK_MAPA_CEDENTE FOREIGN KEY ([ID_CEDENTE])
        REFERENCES dbo.TB_CONEXAO_SFTP ([ID_CEDENTE])
)
GO

/* ---------------------------------------------------------------------
   Registro de arquivos JA transferidos (garante idempotencia).
   NAO e log: e o controle do que ja foi baixado, para nao repetir.
   --------------------------------------------------------------------- */
IF OBJECT_ID('dbo.TB_TRANSFERENCIAS', 'U') IS NULL
CREATE TABLE [dbo].[TB_TRANSFERENCIAS](
    [ID_TRANSFERENCIA] BIGINT IDENTITY(1,1) NOT NULL,
    [ID_MAPA]          BIGINT       NOT NULL,          -- FK -> TB_ARQUIVO_MAPA(ID)
    [ID_CEDENTE]       INT          NULL,              -- redundante p/ consulta rapida
    [NM_ARQUIVO]       VARCHAR(300) NOT NULL,
    [DT_ARQUIVO]       DATE         NULL,              -- data de referencia do arquivo (mtime)
    [TAMANHO_BYTES]    BIGINT       NULL,
    [DT_TRANSFERENCIA] DATETIME     NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_TB_TRANSFERENCIAS PRIMARY KEY ([ID_TRANSFERENCIA]),
    CONSTRAINT FK_TRANSF_MAPA FOREIGN KEY ([ID_MAPA])
        REFERENCES dbo.TB_ARQUIVO_MAPA ([ID]),
    -- Chave de idempotencia: mesmo mapa + nome + data nunca transfere 2x.
    CONSTRAINT UQ_TRANSFERENCIA UNIQUE ([ID_MAPA], [NM_ARQUIVO], [DT_ARQUIVO])
)
GO


/* =====================================================================
   PARTE 2 — Banco LOGS_ROBOS (log de execucao)
   ===================================================================== */
USE [LOGS_ROBOS]
GO
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/* ---------------------------------------------------------------------
   Log de cada execucao (1 linha por processo/mapa executado no disparo).
   ID_EXECUCAO agrupa tudo do mesmo disparo de 10 min.
   --------------------------------------------------------------------- */
IF OBJECT_ID('dbo.TB_LOG_EXECUCAO', 'U') IS NULL
CREATE TABLE [dbo].[TB_LOG_EXECUCAO](
    [ID_LOG]        BIGINT IDENTITY(1,1) NOT NULL,
    [ID_EXECUCAO]   UNIQUEIDENTIFIER NOT NULL,         -- agrupa os processos do mesmo disparo
    [ID_MAPA]       BIGINT           NULL,
    [ID_CEDENTE]    INT              NULL,
    [NM_CEDENTE]    VARCHAR(255)     NULL,
    [DT_INICIO]     DATETIME         NOT NULL,
    [DT_FIM]        DATETIME         NULL,
    [STATUS]        VARCHAR(20)      NOT NULL,          -- SUCESSO | ERRO | SEM_ARQUIVOS
    [QTD_ARQUIVOS]  INT              NOT NULL DEFAULT 0,
    [NM_ARQUIVOS]   VARCHAR(MAX)     NULL,
    [MENSAGEM]      VARCHAR(MAX)     NULL,              -- erro resumido / observacao
    [MAQUINA]       VARCHAR(100)     NULL,
    [DT_REGISTRO]   DATETIME         NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_TB_LOG_EXECUCAO PRIMARY KEY ([ID_LOG])
)
GO
