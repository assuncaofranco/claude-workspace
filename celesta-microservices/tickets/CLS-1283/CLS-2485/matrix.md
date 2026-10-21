# CLS-1283-CLS-2485 — matriz

Status: **assinada pelo Lucas em 2026-10-16** (2–13 confirmados; 6 reclassificado como N).
Escopo e provas: `memory/tasks/CLS-2485/scope.md`. Linhas citadas em `origin/master` de 2026-10-16.

## Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| Vertical do domínio | sportsbook, casino | wallet `TransactionRollbackListener:65` (`isSportsBetting`) |
| Status do sub_balance no rollback | played, outro | wallet `TransactionRollbackListener:74` |
| Valor da aposta de bônus | > 0, 0 | wallet `TransactionRollbackListener:75` |
| `bonusId` do sub_balance | preenchido (bônus da promotion), null (legado só wallet) | wallet `TransactionRollbackListener:89`, `RewardAssetClaimedListener:33` |
| Bônus na promotion ao chegar o job | played, outro status, inexistente | promotion `BonusRollbackJobHandler:13,34`, `BonusBalanceRestoredJobHandler:18,26` |
| Estado das filas no deploy da promotion | vazia, `BonusRollbackJob` em voo, mensagem em `promotion-failed` | `messenger.yaml` wallet:68 (`promotion_bonus_sqs`, FIFO) |
| Ambiente que agenda os commands | prod-1/staging-1/preprods (`celesta-argocd`), prod-2 (`celesta-sb-argocd`) | `e7391a5` no celesta-argocd; `wallet-cronjobs.yaml` no sb-argocd |
| Command | `expire:bonus:offer`, `expire:bonus:validity`, `bonus-model:refresh-state`, `bonus:cancel`, `transaction:adjust-bonus-balance` | wallet `src/AppBundle/Command/` |

## Casos

| # | Célula | Classe | Justificativa | Critério de aceitação |
|---|---|---|---|---|
| 1 | SB × played × aposta > 0 × bonusId preenchido × promotion played | **A** | o caminho que perde o `BonusRollbackJob` | dado um bônus SB played por uma aposta, quando a aposta sofre rollback, então a wallet despacha **só** `BonusBalanceRestoredJob` (nenhum `BonusRollbackJob`) e `GET` do bônus na promotion devolve `status = claimed` |
| 2 | SB × played × aposta > 0 × bonusId null | N | nada era nem é despachado: `notifyPromotion:89` retorna, `RewardAssetClaimedListener:33` pula | — |
| 3 | casino × qualquer | N | `isValidBonusBetRollback:65` exclui; o listener nem age | — |
| 4 | SB × não played, ou aposta = 0 | N | `revertPlayedBonus:74-75` não muda status, nada é despachado | — |
| 5 | promotion com bônus em outro status ao chegar | E → 1 | os dois handlers retornam cedo no mesmo teste (`Rollback:34`, `Restored:26`); PLAYED→CLAIMED é transição válida em `BonusConstants::STATUS_TRANSITIONS`, então a validação de workflow do Restored nunca recusa esse caso | — |
| 6 | promotion sem o bônus | N (com nota) | Lucas: todos os bônus foram migrados para a promotion. Exceção conhecida: ~10 sub_balances órfãos do healthcheck 089 (delta do sync). Para eles a remoção só troca o sinal: antes `Rollback:13` mandava para `promotion-failed`; depois só o log de erro de `Restored:18`. Sem efeito em saldo | — (citar no spec como edge conhecido) |
| 7 | `BonusRollbackJob` em voo no deploy da promotion | **A** (deploy) | handler removido + `max_retries: 0` = mensagem perdida | a promotion só sobe depois que a wallet nova está no ar e a `promotion-bonus.fifo` não tem `BonusRollbackJob` (taxa observada: 1 em 30 dias, só prod-2) |
| 8 | `promotion-failed` com `BonusPlayedJob`/`BonusRollbackJob` | **A** (deploy) | depois do deploy viram mensagens sem classe | triadas e descartadas antes do deploy da promotion |
| 9 | produtor de `BonusPlayedJob` / `BonusClaimedJob` | N | 0 dispatches em 30 dias (APM) e nenhum `new` em nenhum serviço | — |
| 10 | commands no-op × prod-1/staging/preprods | N | CronJobs já removidos em `e7391a5` | — |
| 11 | commands no-op × prod-2 | **A** | CronJobs vivos até o sb-argocd #846 | #846 mergeado antes do deploy da wallet; depois, zero spans `symfony.command` desses nomes em prod-2 |
| 12 | `bonus:cancel` | **A** | removido; substituto é o cancel do BO | `bin/console list` sem `bonus:cancel`; BO `POST /player/{p}/bonus/{b}/cancel` segue cancelando na promotion **e** o sub_balance na wallet |
| 13 | `transaction:adjust-bonus-balance` | N | fica: mexe em sub_balance, não é legado | `bin/console list` ainda tem o command |
| 14 | job-library | **A** | 3 classes removidas, release nova | nenhuma referência às 3 classes em wallet/promotion; os dois composer apontam para a tag nova, não `dev-*` |
| 15 | Behat da promotion (`BonusSteps:903`) | **A** | o cenário de rollback dirige o handler removido | cenário repontado para `BonusBalanceRestoredJobHandler`, verde |
