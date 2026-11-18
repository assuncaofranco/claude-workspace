---
name: cls4314-decisions
description: "CLS-4314 (expedite) — N+1 do transaction report do BO na promotion; decisão: rota bulk por domínio na promotion + BO chama por chunk; varredura de riscos feita 2026-10-30"
metadata:
  node_type: memory
  type: project
  originSessionId: d34c3823-e8f6-442c-ae5f-e331f1339aa3
  modified: 2026-10-30T13:29:54.449Z
---

Expedite, D-Team, assignee Marcello. BO `TransactionReportController::getRewardingByTransactionId` faz 1 POST
à promotion **por player** da página (rota `/api/domain/{d}/player/{p}/rewarding` exige player).

**Decisão (Lucas, 2026-10-30):** só o curto prazo. Rota nova na promotion, por domínio, recebendo **pares**
`{transactionId, playerId}` (até 1000) + `event`: uma query por ids e filtro por par no service, resposta
`RewardingEntry` igual à antiga. BO troca o loop por player por chunk de 1000 pares. O "target" do ticket
(endpoint de rewards no gateway, front monta) fica para outro ticket. Lucas rejeitou paralelizar no BO (piora a
rajada). **Princípio do expedite: a resposta do BO não muda em nada** ([[expedite-scope]]).

**Por que pares e não ids soltos (terceira verificação, 2026-10-30):** o RAF grava o `deposit_success` do
indicado também na promoção do indicante (`ReferAFriend::dispatchRecord`), com o mesmo transactionId. Sem o
filtro de jogador a query devolve as duas e o `rewarding` do BO mudaria. Ver `tickets/CLS-4314/matrix.md`, caso 18.

**Estado 2026-10-30:** spec no Jira (sdd-spec), sub-tasks CLS-4322 (promotion, plano no PR #582) e CLS-4323
(backoffice, plano no PR #3287), 4322 blocks 4323. Pai em Implementing (alguém moveu de manhã). Compêndio do
Notion dá 404 para a nossa conexão — Lucas mandou pular. Próximo: db-query + coleção, depois sdd-implement.

**Estado 2026-10-30 (fim do dia):** código nos dois PRs (promotion #582, backoffice #3287), ambos aprovados pelo
Bohdan antes da última rodada. Virgile recusou mexer na rota por jogador, mesmo por dentro: a rota antiga voltou
byte a byte ao master e a nova tem `findRewardingRowsForPlayers()` + `getRewardingForPairs()` (plano corrigido,
Decisions credita o Virgile). Respondido no PR. Provas: EXPLAIN ANALYZE prod domínio 53 = 30 ms (351 jogadores,
491 depósitos, entra por `idx_player_promotion_configuration`); PP1 domínio 56 página de 1000 em 2,4 s, 41
depósitos RAF sem duplicata; teste de resposta completa no BO passa também contra o código do master; Newman
local em `postman/CLS-4314/` (rota do BO é `bonus_configuration`; esvaziar a fila `dev-promotion` antes).
Pendente: label `sdd-implement`, PR do proteus, testes do PO (Francisco).

**Varredura (origin/master, 2026-10-30):**
- Rota atual tem 3 consumidores além do proteus: BO (transaction report), gateway
  (`PaymentTransactionController`, lista do próprio player) e sportsbetting (`internal/pkg/promotion`, bet).
  Gateway e sportsbetting são de um player só — a rota fica intacta.
- O loop por player não tem outro motivo: o plano `_plans/CLS-594-CLS-1211-2.md` do BO só agrupa porque a
  rota exige player. A spec já pedia "sem número excessivo de chamadas".
- Id do depósito é único global: `DepositJob.transactionId` = `payment.transaction.id` (auto-increment, uma
  tabela para todos os domínios). `Promotion\SuccessfulDepositJob` não tem produtor no master; o
  `Wallet\SuccessfulDepositJob` é outra classe e não chega à promotion. `pe.transactionId` de bet é outro
  espaço de id, mas o filtro `eventType` separa — manter `event` obrigatório na rota nova.
- `promotion_event` tem `idx_transaction_id`; o filtro `pc.domainId` continua.
- Guard HMAC vem de `config/routes.yaml` para todo o ApiBundle: rota nova herda.
- Mudança de comportamento: hoje falha de 1 player zera só as linhas dele; com 1 chamada, uma falha zera o
  rewarding da página inteira (a página continua abrindo). Decisão de produto pendente.
- Testes: BO mocka a URL por player (atualizar); proteus precisa da rota nova ([[proteus-pr-procedure]]).
