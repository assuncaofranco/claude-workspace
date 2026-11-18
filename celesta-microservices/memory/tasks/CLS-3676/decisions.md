---
name: cls3676-decisions
description: "CLS-3676 (promotion money-path idempotency) — escopo do pai, decisão do 409, armadilha da chave de idempotência"
metadata:
  node_type: memory
  type: project
  originSessionId: ce1ff9bf-ec84-4901-ba43-d9604fdb7cab
  modified: 2026-10-27T08:11:14.462Z
---

Pai CLS-3676 é bug report do QA (Francisco, Qase PCPR/265), não spec. Sub-task CLS-4053 (criado pelo Marcello, 2026-10-26) só tem título.

Decisões 2026-10-26 (Lucas):
- Rodar `sdd-spec` no pai, com `ticket-matrix` antes. Guardar o report original num comentário antes de reescrever.
- Item 1 (deposit duplicado) e item 2 (409) ficam **no mesmo pai**. Os 4 achados soltos ficam fora.
- 409: opção B — 409 só para bônus já claimed, OAS ganha 409, PR no proteus ([[project_proteus_pr_procedure]]). É o que a planilha money-path pede. Front não é preocupação nossa; se precisar, ticket para eles.
- Escopo apertado pelo Lucas: played/canceled/expired **continuam 404**; `rewardIds` com `{rc}` sem bônus (também paga em dobro) é **fora**, reportar como ticket novo. Eu tinha inflado o escopo com os dois.
- `Promotion\SuccessfulDepositJob` não tem produtor (payment trocou por `DepositJob` no CLS-1311; origin/master 2026-10-23 sem refs). Caminho vivo = `DepositJobHandler`. O teste PCPR-19 do QA entra pelo job morto.
- Bonus model: não é decisão, segue o padrão do código (marca no mesmo flush do status da promotion).
- Matriz: `claude-workspace/celesta-microservices/tickets/CLS-3676/matrix.md`.

Sem SDD (sem acesso ao Product compendium, etapa do TL): Lucas decidiu corrigir direto e entregar pronto ao Marcello, dizendo que não passou pelo SDD. Branch `CLS-4053` criada do master (4a5fa3996) em 2026-10-27.

Coleção pronta e com baseline (2026-10-27): `postman/CLS-3676/`. Reproduz os dois bugs com os números do QA. Dois achados do ambiente que importam para o ticket:
- **O gateway embrulha todo 4xx da promotion em 404** (`celesta-gateway RewardController.php:46`); o 409 só chega ao player se o gateway mudar. Pendente decisão de escopo.
- A wallet local estava com vendor velho (`ACTION_CLAIMED`), reinstalada com `make init`.
- Primeira rodada do consumer após o push volta vazia no localsqs; o runner re-tenta.

**Estado 2026-10-27:** commit `d2683f2fd` na `CLS-4053` (local, não pushado). Guarda no `processReward` do deposit_tier via `PromotionRepository::hasRewardedPromotionForEvent`; `InvalidBonusException::alreadyClaimed()` → 409, só `claimed`. Coleção 86/0, phpunit 1622/0, behat 1089/0. Lucas: lint pré-existente não importa se não bloqueia o commit (complexidade do `processReward` foi de 7 para 8). Opção 1 no 409: só promotion; o gateway converter 4xx→404 vai como achado no PR. Review (2026-10-27): diff ok célula a célula; faltavam cenários Behat e o corpo do 409 no OAS — adicionados e amendados no commit. Cenários do depósito vivem em `features/standard/reward/deposit_status_events.feature` (caminho `DepositJob`, tx explícito, assert no banco): redelivery, depósito distinto, interleaving 13a; claim 409 e canceled 404 em `features/bonus/automatic/bonus_claim_automatic.feature`. Behat 1094/0. Armadilhas: padrão `promotion(s)` casa "promotion"/"promotions", nunca o literal; a feature do tier só passa na suíte inteira (isolada, até cenários antigos falham); o step "makes a deposit of" usa sempre tx 123 e a config dos steps nasce com limite 1, então redelivery ali é absorvido pelo limite (célula 5), não pela guarda. **PR #574** aberto 2026-10-27 (commit 38745b7e6), com instruções de deploy (só código) e o achado do gateway. Falta: perguntar sobre preprod, avisar o Marcello que não passou pelo SDD, avisar o Francisco que o PCPR-19 entra pelo job antigo.

**Armadilha da chave:** `promotion_event` aponta para a `promotion` (instância), não para a configuration. Unique em (promotion_id, transaction_id) NÃO pega o bug — a 2ª cópia recompensa a promotion re-engajada (109), outra instância. Chave precisa ser transação × configuration × player. E o handler engole Throwable, então violação de unique vira log de erro, não ack limpo. Dedupe só por transactionId quebraria depósito que recompensa N configurations (CLS-2689).

## pp1, 2026-10-27 (branch CLS-4053 via Jenkins)
Coleção `postman/CLS-3676/gen_pp1.py` (player 282570, dom 56). Config `CLS-4053 - test config 1793110738377` (pc com promotions 6063-6065, rc auto 7678, rc direct 7679).
- 2 depósitos reais (`/payment` 200 success): 6063 e 6064 rewarded, 6065 engaged; exatamente 1 bônus rc auto por promotion → sem duplicata. Cada depósito passa por initiated + success da mesma transação, então a célula 13 rodou de verdade.
- Claim D 200; de novo 404, E cancelado 404, desconhecido 404 pelo gateway.
- Em preprod bônus sem wagering vira `played` logo após o claim: o segundo claim de D bate em played (404 legítimo), não no caminho do 409. O 409 não é observável em pp1.
- Redelivery do mesmo depósito (células 1, 11, 12-redelivery, 13a) não é alcançável pelas portas de entrada: ficou coberto só por behat/local e pelo PCPR-19 do QA.
- Célula 11 (1ª metade) em pp1: um depósito real atingindo dois deposit_tier (A: 6066 rewarded/6069 engaged; B: 6067 rewarded/6070 engaged), 2 bônus rc auto; Newman 30/0. Coleção `CLS-4053.pp1-cell11.postman_collection.json` (gerada por `gen_pp1.py`).
