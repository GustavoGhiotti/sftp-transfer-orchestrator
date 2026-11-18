# 03 — Plano de Testes

> **Fase 6 do fluxo.** O objetivo é **provar** que o código faz o que deveria — inclusive quando
> a entrada está errada. Todo caso listado aqui deve ter um teste automatizado correspondente
> sempre que possível.

---

## 1. Estratégia

- **Testes unitários:** regras de negócio isoladas (filtro de arquivos, nomeação, regra do `.zip`,
  trava de execução) — usando **fakes** no lugar de SFTP/SMB/banco reais.
- **Testes de integração:** conexões reais (SFTP, SMB, `pyodbc`) são exercidas na **homologação**
  (Fase 7), com um cedente de teste, pois dependem de infraestrutura e credenciais.
- **E2E:** execução real do `python -m src.main` contra o ambiente de homologação (ver Fase 7).
- **Foco de cobertura:** as regras de negócio testáveis sem infra (o miolo do robô).

## 2. Como rodar os testes

```bash
venv\Scripts\activate
python -m pytest -v
```

## 3. Casos de teste

| ID | O que testa | Pré-condição | Entrada | Resultado esperado | Tipo | Status |
|---|---|---|---|---|---|---|
| CT-01 | `.zip` extrai só o conteúdo (zip não é salvo) | — | zip com `dados.csv` | grava `dados.csv`; registra origem `dados.zip` | Unitário | ✅ |
| CT-02 | Arquivo simples + `RENOMEAR_COM_DATA` | — | `retorno.ret` | grava `retorno_AAAAMMDD.ret` | Unitário | ✅ |
| CT-03 | Idempotência: já transferido não reprocessa | arquivo em `TB_TRANSFERENCIAS` | `dados.zip` | `SEM_ARQUIVOS`, nada gravado | Unitário | ✅ |
| CT-04 | Erro de SFTP não derruba e vira `ERRO` | SFTP inacessível | conexão falha | `status=ERRO`, sem exceção | Unitário | ✅ |
| CT-05 | Filtro por padrão/data/já-transferidos | — | lista mista | só o pendente do dia que casa o padrão | Unitário | ✅ |
| CT-06 | `_casa_padrao`: `*.zip`, `.ret`, `remessa_*.csv` | — | vários nomes | casa/《não casa》corretamente | Unitário | ✅ |
| CT-07 | Trava bloqueia 2ª execução simultânea | lock ativo | 2º `adquirir()` | retorna `False` | Unitário | ✅ |
| CT-08 | Lock morto (idade) / ilegível é assumido | lock velho/corrompido | `adquirir()` | retorna `True` | Unitário | ✅ |

> Legenda de status: ⬜ pendente · 🟨 em execução · ✅ passou · ❌ falhou

## 4. Casos de erro e borda (obrigatório pensar)

- **Entrada vazia / nula:** lista de arquivos vazia → `SEM_ARQUIVOS` (CT-05).
- **Serviço externo indisponível:** SFTP fora → `ERRO` logado, sem derrubar os outros mapas (CT-04).
- **Duplicidade:** arquivo já transferido não é reprocessado (CT-03) + `UNIQUE` no banco.
- **Concorrência:** dois disparos ao mesmo tempo → trava bloqueia o 2º (CT-07); lock morto é
  assumido para não travar o robô (CT-08).
- **Arquivo em upload:** `validar_arquivo_pronto` evita baixar arquivo truncado (verificado na
  homologação, pois depende do SFTP real).

## 5. Evidências

Saída de `python -m pytest -v` (2026-08-14):

```
platform win32 -- Python 3.12.10, pytest-8.4.2
collected 16 items

tests/test_file_lock.py ....                                     [ 25%]
tests/test_filtro.py ........                                    [ 75%]
tests/test_transferencia.py ....                                 [100%]

============================= 16 passed in 0.86s ==============================
```

## 6. Resultado

- Total de casos: 16 · Passaram: 16 · Falharam: 0
- Escopo coberto: regras de negócio (filtro, `.zip`, rename, idempotência, trava).
- Pendências conhecidas: integração real (SFTP/SMB/banco) validada na homologação (Fase 7).

---

**Critério de pronto (Fase 6):** casos principais e de erro cobertos, testes passando e
cobertura mínima atingida. Só então avança para a homologação.
