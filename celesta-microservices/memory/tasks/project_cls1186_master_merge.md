---
name: project_cls1186_master_merge
description: "CLS-1186 (potential winnings, celesta-promotion PR #442) — master merge após 2 meses; master já tinha reimplementado quase toda a plumbing da branch"
metadata: 
  node_type: memory
  type: project
  originSessionId: a6c580fa-781f-42c7-a3ed-acf00d5bae40
  modified: 2026-09-16T14:08:58.669Z
---

CLS-375-CLS-1186 (celesta-promotion, PR #442, `potentialWinnings` no `/rewarding`) estava 444 commits atrás de master. Merge feito e pushado em 2026-09-15 (commit `4dbc0b972`), PHPUnit 1599/1599 verde.

## O bug que o merge introduziu (achado e corrigido em 2026-09-16, commit `f929e2934`)

**A decisão 1 abaixo — manter a query do master — matou a feature.** `REWARDING_EVENT_NAMES_BY_TYPE` é `bet → [bet_settled]`, e uma aposta ainda `pending` grava **só** `bet_pending`. Resultado: a aposta em voo — exatamente o caso que o `potentialWinnings` existe para cobrir — era estruturalmente invisível ao `/rewarding`. Sobrava só a janela estreita de um `bet_settled` numa promoção ainda `engaged` (Multiplus incompleto); no caso principal (FBI) o campo nunca aparecia.

Correção (PO confirmou incluir pending): constante **separada** `PromotionEvent::IN_FLIGHT_EVENT_NAMES_BY_TYPE` (`bet → [bet_pending]`), e `findRewardingRows()` casa a união das duas. **Separada de propósito** — `REWARDING_EVENT_NAMES_BY_TYPE` também alimenta `findLatestByPromotionIds()`, que é o campo `event` de traceability do CLS-931; alargar no lugar faria aquele campo passar a apontar para eventos pending. Mortos (`rejected`/`failed`/`timeout`/`canceled`) ficam fora dos dois. Depósito não precisa de nome in-flight: a janela engaged dele abre no `deposit_success`, que já casa.

**Lição generalizável:** quando um endpoint tem duas metades mutuamente exclusivas decididas por status (aqui `rewards` vs `potentialWinnings`), elas podem precisar de **conjuntos de eventos opostos** — a metade "já aconteceu" quer o evento terminal, a metade "vai acontecer" quer o evento em voo. Herdar o filtro de uma delas silencia a outra sem erro nenhum. Ver também [[feedback_review_product_impact_not_just_current_code]].

**Como foi achado:** teste real no preprod-1 com Newman (player 282577, domínio **213 = Sportsbook**, não o 56 default), aposta #121 `pending` → BO devolveu `rewarding: []`. Ver [[project_cls1186_preprod_newman]].

## O achado que definiu o merge

Master reimplementou, melhor, quase toda a infra de traceability que a branch carregava — linhas CLS-594-CLS-928/929/931-2 e CLS-1310. Resolução: **master ganha em tudo que é traceability**, só o delta real do 1186 volta por cima. Diff contra master caiu de 73 arquivos para 11.

O que foi descartado da branch (tudo superseded):
- `EventBuilder` — mesmo arquivo dos dois lados; o do master resolve N+1 (`findLatestByPromotionIds`) e tira o tipo do evento gravado, não da config
- `BonusNormalizer` event enrichment, `PromotionEventNormalizer`, `PromotionNormalizer`, `ReferralRepository`
- `recordTransactionEvent()`/`recordPromotionEvent()` no reward path — master grava via `PromotionEventRecorder` + operação `Record` (CLS-1309/1310); manter os dois grava `promotion_event` **duplicado**
- `PromotionConfiguration::getEventType()` — sem call site após o merge
- `MultibetWonJobHandler` — deletado em master (consolidado no `SportsbettingBetJobHandler`, CLS-1310); a branch só mudava `const` → `const float`

## Decisões de código tomadas no merge

1. **`RewardingService` fica sobre o `findRewardingRows()` do master** (filtra por `eventName` em `PromotionEvent::REWARDING_EVENT_NAMES_BY_TYPE`, array result sem hidratação) em vez do `findByTransactionIds()` da branch (filtrava por *tipo de configuração* — regra mais frouxa, deixava passar evento de ciclo de vida). Query ganhou `MAX(pe.id) AS promotionEventId` com `GROUP BY (transactionId, promotionId, pcId)` — preserva a cardinalidade que o `DISTINCT` dava e resolve o edge case de múltiplos eventos por par. Novo `PromotionEventRepository::findByIds()` carrega só os eventos apontados.
2. **`PotentialWinningsCalculator::resolveModel()` passou a usar `RewardSourceResolver`** (escolha do Lucas) em vez de `em->find(RewardConfiguration, bonusModelId)` / chamada à Wallet à mão. Ganha checagem de domínio **e conserta bug real**: a versão da branch pulava (`continue`) todo reward com `bonusModelId === null`, que pós-cutover é todo reward ligado direto a uma `RewardConfiguration` — contribuiriam zero silenciosamente.
3. Removidos do merge por serem ruído fora de escopo: `FeatureFlagService::isMoveBonusToPromotionEnabled()` (ficou sem caller) e a linha `$promotion->addPromotionEvent($this)` no construtor de `PromotionEvent`.

Tudo isso está escrito na seção **"As-built deviations (master merge, 2026-09-15)"** de `sdd/_specs/CLS-1186.md` — é lá que mora o detalhe, não aqui.

## Modelo confirmado com o Lucas (vale além deste ticket)

A flag `move_bonus_to_promotion` **só decide a origem do bônus**, não o sistema de reward:
- `Reward` (quantity/options/type na promotion configuration) é config da própria promotion, independente de flag → `potentialWinnings` **não tem gate**, lê `Reward` + `promotion_event.transaction_data`, nunca a tabela `bonus`
- `RewardOfferService::offerReward()` retorna `null` com a flag off (criar o `Bonus` ali creditaria o jogador duas vezes — a Wallet já oferece e claim'a)
- o único ponto do cálculo que depende da flag é resolver o model do bônus, que é exatamente o trabalho do `RewardSourceResolver`

## Gap aberto (não é deste ticket, precisa de ticket próprio)

Com a flag off, o campo `rewards` do `/rewarding` retorna **sempre `[]`** — master não faz fallback pra buscar na Wallet, e a Promotion não tem lookup pra isso (não conhece o id do bônus emitido lá). Veio do CLS-594-CLS-931-2. Contraria o modelo do Lucas ("flag off → busca na wallet") e o time de SB já está integrando contra esse endpoint, ou seja, metade da resposta é inerte até o cutover. Ver [[project_bonus_model_field_removal_risk]].

## Estado do repo deixado para trás

- checkout principal do celesta-promotion ficou **na `CLS-375-CLS-1186`** (estava na `CLS-1843-CLS-1912-support-bonus-without-currency`)
- as 2 linhas não commitadas da CLS-1843 (`celesta-fixtures` `v1.221` → `^1.221` em composer.json/lock) foram **descartadas do working tree** e salvas em patch no scratchpad da sessão — se a sessão sumiu, é só refazer a mão, é uma linha
- branches irmãs do CLS-375 **não** foram mergeadas (decisão do Lucas): celesta-backoffice #3051 e celesta-gateway #1411 (CLS-1324, time de SB, 879/358 commits atrás), celesta-backoffice-front CLS-1218 (time de front, 22 atrás)

## Gotcha de processo

Worktree isolado (`git worktree`) para não sujar o checkout principal **não tem `vendor/`** → o hook de pre-commit (phpinsights) não roda e os testes não rodam (o container monta o checkout principal). Symlinkar o vendor destrava o hook, mas `.gitignore` tem `/vendor/` com barra, que **não casa symlink** — o link entra no commit via `git add -A`. Aconteceu aqui, corrigido com `git rm --cached vendor` + `--amend`. Ver [[feedback_make_init_after_branch_switch]].
