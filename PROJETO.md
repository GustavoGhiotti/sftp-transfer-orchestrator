# PROJETO — Manifesto do Padrão de Desenvolvimento

> **Arquivo base do Grupo Acme.** Copie este arquivo (e a pasta `docs/`) para a raiz de
> todo projeto novo. Ele descreve *como o projeto deve ser construído, documentado, testado
> e homologado*. Tanto uma pessoa quanto uma IA (como o Claude) devem ler este arquivo
> **antes de escrever qualquer código** e seguir o fluxo definido aqui.

---

## 0. Como usar este arquivo

1. Copie o kit padrão para a raiz do projeto (`PROJETO.md` + pasta `docs/`).
2. Preencha a seção **1. Identidade do Projeto** abaixo.
3. Siga o **fluxo de desenvolvimento** (seção 3), fase por fase, sem pular etapas.
4. Cada fase só é considerada concluída quando o seu **critério de pronto** for atendido.
5. Ao final, o projeto só é entregue depois de **homologado** (seção 4 e `docs/04-HOMOLOGACAO.md`).

> **Instrução para IA / assistente:** ao receber um projeto que contém este arquivo, leia-o
> por completo, confirme em qual fase o projeto está, e conduza o trabalho respeitando a
> ordem das fases e os critérios de pronto. Nunca comece pela implementação do código sem
> antes ter o diagrama (Fase 1) e a definição de estrutura e stack (Fases 2 e 3).

---

## 1. Identidade do Projeto

| Campo | Valor |
|---|---|
| **Nome do projeto** | _(a definir — proposta: RoboTransferenciaSFTP)_ |
| **Tipo** | **Script/Automação** |
| **Responsável** | Equipe de Desenvolvimento (desenvolvimento@empresa.example) |
| **Data de início** | 2026-08-14 |
| **Objetivo (1 frase)** | Baixar arquivos do SFTP de cada cliente e gravá-los em destino SMB local, orquestrado, idempotente e logado, a cada 10 min. |
| **Stakeholders** | Área que consome as cargas / Equipe de Desenvolvimento |
| **Projeto no Jira (chave)** | _(a definir — chave do card, ex.: KAN-0000)_ |
| **Status atual** | Fase 1 ✅ · Fase 2 ✅ · Fase 3 ✅ · Fase 4 ✅ · Fase 5 ✅ · Fase 6 ✅ · **Fase 7 (homologação)** |
| **Repositório** | _(a definir)_ |
| **Versão atual** | v0.1.0 |

---

## 2. Princípios

- **Nada sem diagrama.** Todo projeto começa desenhando a estrutura/fluxo antes do código.
- **Documentar enquanto se constrói**, não depois. A documentação faz parte do código.
- **Não existe "pronto" sem teste e sem homologação.** Funcionar na sua máquina não basta.
- **Padrão acima de preferência pessoal.** Um projeto do Grupo Acme deve ser reconhecível
  por qualquer pessoa da equipe.
- **Reversível e rastreável.** Tudo versionado no Git e ligado a um ticket do Jira.

---

## 3. Fluxo de Desenvolvimento (7 Fases)

O desenvolvimento segue **sempre** esta ordem. Cada fase tem um entregável e um critério de pronto.

### Fase 1 — Diagrama e Estrutura
**Objetivo:** entender o problema e desenhar a solução antes de codar.
**Entregável:** `docs/01-ARQUITETURA.md` com diagrama (Mermaid) da estrutura e do fluxo principal.
**Critério de pronto:** o diagrama mostra os componentes, como se comunicam e o fluxo de dados
de ponta a ponta; foi revisado com o responsável.

### Fase 2 — Estrutura do Código
**Objetivo:** definir a organização de pastas e arquivos.
**Entregável:** esqueleto de pastas criado no repositório, seguindo o padrão da seção 5.
**Critério de pronto:** a árvore de pastas existe e reflete o diagrama da Fase 1.

### Fase 3 — Definição de Stack e Dependências
**Objetivo:** decidir o que será utilizado (linguagem, frameworks, libs, serviços).
**Entregável:** seção "Stack" preenchida em `docs/02-DOCUMENTACAO.md` + arquivo de dependências
(`package.json`, `requirements.txt`, `.csproj`, etc.).
**Critério de pronto:** toda dependência tem uma justificativa de 1 linha; versões fixadas.

### Fase 4 — Documentação
**Objetivo:** documentar visão, como rodar e como usar, antes de a implementação avançar muito.
**Entregável:** `docs/02-DOCUMENTACAO.md` preenchido (visão geral, instalação, uso, contratos/endpoints).
**Critério de pronto:** um dev novo consegue clonar, instalar e rodar só lendo a documentação.

### Fase 5 — Código
**Objetivo:** implementar seguindo a estrutura e a documentação já definidas.
**Entregável:** código-fonte funcional na estrutura da Fase 2.
**Critério de pronto:** funcionalidades do objetivo implementadas; segue as convenções da seção 6;
sem código morto ou credenciais no repositório.

### Fase 6 — Testes
**Objetivo:** provar que o código faz o que deveria.
**Entregável:** testes automatizados + `docs/03-PLANO_DE_TESTES.md` preenchido.
**Critério de pronto:** casos principais e de erro cobertos; testes passando; cobertura mínima
acordada atingida.

### Fase 7 — Homologação
**Objetivo:** comprovar o funcionamento de forma verificável, com evidências.
**Entregável:** `docs/04-HOMOLOGACAO.md` preenchido, com checklist assinado e evidências (prints/logs).
**Critério de pronto:** todos os critérios de aceite marcados; evidências anexadas; aprovado pelo
responsável. **Só depois disso o projeto é considerado entregue.**

---

## 4. Definição de Pronto (Definition of Done)

Um projeto **só está pronto** quando **todos** os itens abaixo forem verdadeiros:

- [ ] Diagrama de arquitetura existe e está atualizado.
- [ ] Estrutura de pastas segue o padrão.
- [ ] Stack e dependências documentadas e justificadas.
- [ ] Documentação permite rodar o projeto do zero.
- [ ] Código segue as convenções.
- [ ] Testes automatizados passando.
- [ ] Homologação concluída, com evidências e aprovação.
- [ ] Ticket(s) do Jira no status concluído.
- [ ] Histórico de decisões preenchido (toda troca/limitação registrada).
- [ ] Nada sensível (senha, token, chave) versionado.

---

## 5. Padrão de Estrutura de Pastas

Estrutura mínima comum a **todos** os projetos:

```
projeto/
├── PROJETO.md              # este arquivo
├── README.md               # visão rápida e como rodar
├── docs/                   # documentação do padrão
│   ├── 01-ARQUITETURA.md
│   ├── 02-DOCUMENTACAO.md
│   ├── 03-PLANO_DE_TESTES.md
│   └── 04-HOMOLOGACAO.md
├── src/                    # código-fonte
├── tests/                  # testes automatizados
└── .gitignore
```

Variações por tipo de projeto estão detalhadas no `README.md` (seção "Estrutura por tipo").

---

## 6. Convenções

**Nomenclatura**
- Pastas e arquivos em `kebab-case` ou o padrão idiomático da linguagem (ex.: `PascalCase` para classes).
- Nada de nomes genéricos como `teste2`, `final`, `novo`.

**Git + Jira** (todo trabalho é rastreado por um ticket do Jira)
- Branch principal: `main`. **Toda branch de trabalho começa pela chave do ticket do Jira**,
  para o Jira linkar automaticamente o desenvolvimento ao card:
  `feature/KAN-0000-login`, `bugfix/KAN-0000-calculo-imposto`, `hotfix/KAN-0000-...`, `docs/KAN-0000-...`
  (a chave `KAN` é o padrão; se o projeto tiver outra chave no Jira, use a dele).
- **Todo commit começa com a chave do ticket**, assim o Jira mostra o commit dentro do card.
  Padrão (chave do ticket + Conventional Commits):
  `KAN-0000 feat: adiciona endpoint de login`, `KAN-0000 fix: corrige cálculo de imposto`,
  `KAN-0000 docs: atualiza README`.
- **Smart Commits do Jira** (opcional, muito útil): dá para comentar, apontar tempo e mover o
  card direto pela mensagem do commit —
  `KAN-0000 #comment ajuste na validação #time 2h #done`.
- **Pull Request:** o título também leva a chave do ticket (ex.: `KAN-0000 Adiciona login`) e o
  card do Jira deve ser referenciado na descrição. Só faça merge com o ticket no status correto.
- **Regra de ouro:** sem ticket do Jira, não abre branch nem faz commit — tudo tem que ficar
  visível e rastreável no card.

**Versionamento (SemVer)**
- `MAJOR.MINOR.PATCH` (ex.: `1.4.2`). Quebra de compatibilidade sobe MAJOR; nova função sobe MINOR;
  correção sobe PATCH.

**Segurança**
- Segredos em variáveis de ambiente (`.env`), **nunca** no código. `.env` sempre no `.gitignore`.
- Um `.env.example` documenta as variáveis necessárias, sem os valores reais.

---

## 7. Histórico de Decisões (obrigatório)

Registre **toda** decisão importante de arquitetura/tecnologia aqui, para não se perder o "porquê".
É **obrigatório registrar sempre que houver uma troca** — por exemplo, quando o projeto foi feito
e apresentou uma limitação (velocidade, desempenho, custo, etc.) e por isso uma tecnologia ou
abordagem foi substituída. Descreva **o que mudou, o motivo e o impacto** da mudança.

| Data | Decisão | Motivo / Limitação encontrada | O que substituiu | Impacto |
|---|---|---|---|---|
| 2026-08-14 | Orquestrador único disparado pelo agendador | Modelo atual (vários `.bat` por processo no RoboCargas) causa disparos redundantes e sobrecarga | Múltiplos `.bat` | Centraliza controle, evita reprocesso, um só ponto de log |
| 2026-08-14 | Unidade de controle por **mapeamento de arquivo** (`TB_ARQUIVO_MAPA`) | Precisão fina: mesmo cliente com vários arquivos/destinos | Controle por cliente/ID_CEDENTE (RoboCargas) | Cada arquivo controlado e logado à parte |
| 2026-08-14 | "Concluído" = **idempotência por arquivo** (`TB_TRANSFERENCIAS`) | Não travar o dia; pegar arquivos que chegam mais tarde | Marcar done após 1 sucesso no dia | Retransferência nunca ocorre; retenta o que falhou |
| 2026-08-14 | Execução em **pool paralelo limitado** | Muitos clientes; ganho de tempo mantendo consumo sob controle | Execução sequencial | Ciclo de 10 min mais folgado |
| 2026-08-14 | Log em banco **`LOGS_ROBOS`** (servidor .66, conexão separada) | Log centralizado da empresa, isolado da config | Log no mesmo banco da config | Duas conexões pyodbc (config + logs) |
| 2026-08-14 | Config em banco novo **`DB_SFTP`**; vínculo por **`ID_CEDENTE`** | Organizar as tabelas do robô fora do `DB_DESENVOLVIMENTO` legado | Tabelas no banco legado | 3 tabelas próprias (conexão, mapa, transferências) |
| 2026-08-14 | Comportamento **orientado a dados** (flags no `TB_ARQUIVO_MAPA`) | Evitar criar código para cada novo processo | `TIPO_PROCESSO` com `if/else` no código | Novo processo = nova linha; etapas genéricas ligadas por flags |

---

_Padrão Grupo Acme · v1.0 · mantido pela equipe de Desenvolvimento._
