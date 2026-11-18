# 04 — Homologação

> **Fase 7 do fluxo — a última.** Homologar é **comprovar**, com evidências, que o projeto
> funciona conforme o combinado. Não basta "rodou aqui": cada critério precisa de prova
> (print, log, vídeo) e de aprovação do responsável. **Sem homologação, o projeto não é entregue.**

---

## 1. Dados da homologação

| Campo | Valor |
|---|---|
| Projeto | _(nome)_ |
| Versão homologada | _(ex.: v1.0.0)_ |
| Ambiente | _(homologação / staging)_ |
| Data | _(preencher)_ |
| Homologado por | _(nome do responsável)_ |
| Executado por | _(quem rodou os testes)_ |

## 2. Critérios de aceite

Cada linha é um requisito acordado. Marque como aprovado **somente com evidência anexada**.

| ID | Critério de aceite | Como comprovar | Evidência | Status |
|---|---|---|---|---|
| CA-01 | _(ex.: usuário consegue fazer login)_ | Print da tela + log | _(link/anexo)_ | ⬜ |
| CA-02 | _(ex.: relatório gera com dados corretos)_ | Arquivo gerado conferido | | ⬜ |
| CA-03 | _(ex.: erro de senha mostra mensagem clara)_ | Print do erro | | ⬜ |
| CA-04 | _(ex.: tempo de resposta aceitável)_ | Log de tempo | | ⬜ |

> Status: ⬜ pendente · ✅ aprovado · ❌ reprovado

## 3. Checklist final de entrega

- [ ] Todos os critérios de aceite aprovados, com evidências.
- [ ] Testes automatizados passando (ver `03-PLANO_DE_TESTES.md`).
- [ ] Documentação permite instalar e rodar do zero (ver `02-DOCUMENTACAO.md`).
- [ ] Diagrama de arquitetura atualizado (ver `01-ARQUITETURA.md`).
- [ ] Nenhum segredo (senha/token/chave) versionado.
- [ ] Versão marcada no Git (tag) e changelog atualizado.
- [ ] Responsável revisou e aprovou.

## 4. Evidências anexadas

_(Liste aqui os prints, logs, vídeos ou links que comprovam cada critério.)_

1. _(ex.: `evidencias/login-sucesso.png`)_
2. _(...)_

## 5. Pendências e ressalvas aceitas

_(Bugs conhecidos ou itens adiados que o responsável aceitou liberar mesmo assim.)_

| Item | Impacto | Prazo para resolver |
|---|---|---|
| _(...)_ | | |

## 6. Parecer final

- [ ] **APROVADO** — projeto homologado e liberado.
- [ ] **APROVADO COM RESSALVAS** — liberado com as pendências da seção 5.
- [ ] **REPROVADO** — retornar para correção (descrever motivo abaixo).

**Motivo / observações:** _(preencher)_

Assinatura do responsável: ______________________  Data: ____/____/____

---

**Critério de pronto (Fase 7):** parecer APROVADO (ou com ressalvas aceitas), todas as evidências
anexadas. A partir daqui o projeto está oficialmente **entregue**.
