# CLS-3676 — matriz de variantes

Pai CLS-3676, sub-task CLS-4053. celesta-promotion lido no branch `CLS-1283-CLS-2485` (2026-10-26).
Estado: **classificação proposta, aguardando sign-off do Lucas.**

Escopo (Lucas, 2026-10-26): item 1 = o mesmo depósito não premia duas vezes; item 2 = 409 só para bônus
`claimed`. O resto vai para "Fora do escopo", no fim.

## Item 1 — depósito entregue duas vezes

### Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| Job de entrada | `DepositJob` status success · `Promotion\SuccessfulDepositJob` | `DepositJobHandler.php`, `SuccessfulDepositJobHandler.php`. Produtor: só a payment, e só do `DepositJob` (`TransactionSubscriber.php:319`, desde CLS-1311 99df3067b 2026-06-22). `git grep SuccessfulDepositJob origin/master` na payment (81f212a8f, 2026-10-23) = 0. O `Wallet\SuccessfulDepositJob` é outra classe, roteada para `crm_sqs` (`celesta-wallet/config/packages/messenger.yaml:47`) |
| Tipo de configuration que reage a depósito ok | `deposit_tier` · `refer_friend` | `PromotionConfigurationTypeFactory::createFromEvent`; `DepositTier.php:27`, `ReferAFriend.php:64` |
| Depois do reward, re-engaja o player? | sim (`rewarding_limit` null, abaixo do limite, ou scope occurrence) · não | `Standard\Handler\RewardHandler.php:120-130`; a instância já premiada é barrada em `isPromotionEligible:195` |
| Configurations atingidas pelo depósito | 1 · N | loop em `Standard.php:111` |
| Entrega da cópia | concorrente · sequencial | lock `deposit-reward-lock-{transactionId}` |
| `claiming_event` do reward | `automatic` · `direct` | bônus nasce `offered` (`RewardOfferService.php:136`); automatic vira claimed no `BonusListener.php:53-56` |
| Fonte do reward | reward configuration · wallet bonus model | `RewardHandler.php:230-253` |
| `rewardIds` no job | ausente · `{rc}_{bonusId}` | `DepositRewardClaimService.php:112-121` (o `{rc}` sem bônus está fora do escopo, ver fim) |
| Status anteriores da mesma transação | só success · initiated/pending antes | `DepositJobHandler::EVENT_BY_STATUS`; `DepositTier.php:25-26` grava `Record` com o mesmo `transaction_id` |
| Outro depósito | mesmo `transactionId` · diferente | fronteira da regra |

### Casos

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 1 | DepositJob × deposit_tier × re-engaja × sequencial × automatic × reward configuration | A | caminho vivo; a 2ª cópia acha a promotion re-engajada (outra instância) e premia | dado player engajado num deposit_tier com `player_promotion_limit: 2` e reward automatic, quando o mesmo `DepositJob` success (mesmo `transactionId`) é consumido duas vezes, então o player tem **um** bônus claimed, a wallet recebe **uma** transação de claim, e a configuration tem `reward_count = 1` |
| 2 | `Promotion\SuccessfulDepositJob` | E → 1 | sem produtor em produção (ver dimensão; Go services também 0 refs). Mas a automação do QA manda exatamente esse job (`celesta-qaa-proteus/src/tests/celesta-promotion/scenario/sameDepositOffersOneBonus.pcpr-19.test.ts:238`), então o re-teste do PCPR-19 passa por ele. A guarda tem de ficar no caminho comum aos dois handlers (dispatch do reward), não em `DepositJobHandler` | — (coberto pelo 1 se a guarda for comum) |
| 3 | `claiming_event: direct` | E → 1 | mesmo `issuePlayerBonuses:219`; muda só o observável | observável do 1 vira: **um** bônus `offered` |
| 4 | fonte = wallet bonus model | E → 1 | mesmo `issuePlayerBonuses`, reward via `postOfferBonusModel:243`; não há `Bonus` na promotion, então a guarda fica no nível promotion/evento, no mesmo flush do status (padrão de `RewardHandler.php:115-118`) | observável do 1 vira: a wallet recebe **um** offer |
| 5 | não re-engaja (`player_promotion_limit: 1`) | N | 2ª cópia não acha promotion engajada; a premiada é barrada em `isPromotionEligible:195` | — |
| 6 | `rewarding_limit` null | E → 1 | mesmo `reengagePlayer`, via `RewardHandler.php:121` | — |
| 7 | scope occurrence | E → 1 | `reengagePlayer` via `RewardHandler.php:129` | — |
| 8 | refer_friend | N | não re-engaja: `updateStatusesAndCounters` vazio (`ReferAFriend/Handler/RewardHandler.php:162-166`), as duas promotions viram `rewarded` (`:258`), e a 2ª cópia filtra `engaged` (`PromotionRepository.php:245`) | — |
| 9 | refer_friend com um papel `bonus_offer_allowed = false` | N | a promotion bloqueada fica `engaged`, mas a do outro papel já é `rewarded`: a busca do referrer filtra `engaged` (`PromotionRepository.php:293`) e a do referee também (`:245`); a 2ª cópia para | — |
| 10 | concorrente | E → 1 | o lock serializa; depois dele, caminho do 1 | — |
| 11 | depósito atinge N configurations | A | dedupe só por `transactionId` mataria o 2º reward legítimo | dado player engajado em dois deposit_tier, quando um depósito chega, então um bônus de cada; quando o mesmo depósito chega de novo, então nenhum bônus novo |
| 12 | outro `transactionId` | A | fronteira: depósito distinto continua premiando | dado o cenário do 1 após o primeiro reward, quando chega um depósito com outro `transactionId`, então a promotion re-engajada é premiada |
| 13 | initiated/pending antes do success | A | `promotion_event` já tem uma linha por status com o mesmo `transaction_id`; a guarda não pode tratar essas linhas como "já premiado" | dado `DepositJob` initiated e pending consumidos, quando chega o success da mesma transação, então o player é premiado |
| 13a | `tx1` initiated, depois outro depósito `tx0` success premia a promotion, depois `tx1` success | A | a promotion premiada por `tx0` já carrega um evento de `tx1` (o initiated). Uma guarda que olhe só o `transaction_id` numa promotion `rewarded` diria "já premiado" e `tx1` nunca pagaria. A guarda tem de olhar evento **success** (`EVENT_NAME_DEPOSIT_SUCCESS`, já existe nas constantes) | dado `tx1` initiated consumido, depois `tx0` success premiando a promotion, quando chega `tx1` success, então a promotion re-engajada é premiada |
| 14 | `rewardIds` `{rc}_{bonusId}` | N | `resolveBonus` só acha `offered` (`DepositRewardClaimService.php:116-121`) | — |
| 15 | valor negativo | N | early return | — |
| 16 | failed/timeout | N | só `Record` + `Expire`, sem reward | — |

## Item 2 — claim repetido

### Dimensões

| Dimensão | Valores | Fonte |
|---|---|---|
| Status do bônus no 2º claim | claimed · played · canceled · expired · inexistente · de outro player | `BonusConstants::STATUSES`; hoje todos dão 404 em `RewardClaimValidator.php:100-108` |
| Forma do `rewardId` | `{rc}_{bonusId}` · `{rc}` | `RewardClaimValidator.php:34-40` |
| Lista | um id · mista | `RewardController.php:424` → `:434` |

### Casos

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 17 | claimed × `{rc}_{bonusId}` | A | pedido da planilha (PCPR-21). Tipos `free` e `free_rounds` (`RewardClaimValidator.php:79`). **O gateway converte todo 4xx da promotion (exceto 403) em 404** (`celesta-gateway/src/Promotion/Controller/RewardController.php:33-46`): o 409 da promotion só chega ao player se o gateway passar a repassá-lo. Decisão de escopo pendente (Lucas) | dado bônus já claimed pelo player, quando `POST .../reward/bonuses/claim` com `["{rc}_{bonusId}"]`, então 409 e nenhuma transação de claim é despachada |
| 18 | played · canceled · expired | A | regressão: fora do pedido, o contrato atual fica | continua 404 `Bonus not found.` |
| 19 | inexistente · de outro player | A | regressão: o 409 não pode revelar bônus de outro player | continua 404 `Bonus not found.` |
| 20 | `{rc}` repetido | N | não há bônus para conflitar | — |
| 21 | lista mista | E → 17 | lista validada inteira antes de clamar (`RewardController.php:424`), validator lança no primeiro inválido | — |

## Coleção — baseline antes do código (2026-10-27)

`postman/CLS-3676/` (`gen.py`, `run.sh`, runbook). Rodada 4, código do master: setup e opt-in verdes; as células 1, 11, 12, 13 e 13a falham com exatamente +1 reward por redelivery (2/2/4, 3/3/6, 4/4/8, 6/6/12 e limite 6 esgotado); na pasta 7 só o 409 falha (404 hoje), 18 e 19 passam. Armadilhas do local: a primeira rodada do `messenger:consume` logo após o push costuma voltar vazia (o runner re-tenta até a fila zerar); a wallet local respondia 500 por `BonusTransactionConstants::ACTION_CLAIMED` indefinido (vendor velho na branch `CLS-3150`), então o `sub_balance` ficou sem linhas até o `make init` da wallet.

## Review (2026-10-27) — fechado

Diff conferido célula a célula: A (1, 11, 12, 13, 13a, 17, 18, 19) com caminho de código e rodada verde na coleção (86/0); E → 1 mantidos (guarda antes de `issuePlayerBonuses`, comum aos dois handlers); N intocados. Achados do review, corrigidos no mesmo commit: faltavam cenários de aceitação (3 no `DepositJob`, 2 no claim) e o OAS publicava o 409 sem corpo. Nenhuma variante nova: o review não achou dimensão que a enumeração tivesse perdido.

## Merge do master (2026-10-27)

O CLS-3833 removeu o `RewardSourceResolver` e o caminho `postOfferBonusModel`: todo reward é bônus local da promotion. A dimensão "Fonte do reward" ficou com um valor só, então a célula 4 (bonus model) deixou de existir, e com ela a janela "wallet respondeu, flush caiu". A guarda e os testes passaram intactos pelo merge.

## Fora do escopo — reportar, não corrigir

- **Grave, dinheiro:** `rewardIds` com `{rc}` sem bônus num depósito entregue duas vezes cria um bônus novo por cópia (`RewardOfferService.php:45`); só `occurrences` segura. Mesmo defeito por outra porta. Candidato a ticket próprio.
- `SuccessfulDepositJobHandler` sem produtor: remoção é cleanup. Avisar o Francisco: a automação (PCPR-19) manda um job que a payment parou de mandar em 2026-06 (CLS-1311); o caminho de produção é o `DepositJob`.
- `RewardHandler.php:120-130`: sem `rewarding_limit`, `reengagePlayer` roda duas vezes.
- RAF: um papel com `bonus_offer_allowed = false` deixa a promotion dele `engaged` para sempre.
- Desenho para o plano, **"já gravado" ≠ "já premiado"**: na mesma entrega, `Record` roda antes de `Reward` (`DepositTier.php:27`, ordem em `Standard.php:61-69`) e grava `promotion_event` com o mesmo `transaction_id`. Uma guarda que leia "existe evento desta transação" bloqueia a **primeira** entrega. A guarda precisa de marca própria de reward.
- Desenho escolhido (Lucas, 2026-10-26), **sem marca nova**: a guarda pergunta "existe promotion `rewarded` desta configuration e deste player com evento `deposit_success` desta transação?". Primeira entrega: a promotion ainda é `engaged`, resposta não, premia. Redelivery: a 105 já é `rewarded` com o evento, resposta sim, ignora. Sem constante nova, sem migration. O filtro pelo nome do evento é obrigatório (13a).
- Desenho para o plano, **sem unique no banco**: o lock por transação (handlers) mais o lock por configuration (`RewardHandler.php:263-292`) já serializam tudo que importa, **entre pods**: o store é `RedisStore` sobre `local_redis` (`services.yaml:71-74`), e em todos os ambientes esse host é um Valkey externo por ambiente, não por pod (`celesta-argocd-parameters/{prod-1,prod-2,preprod-*}/promotion/parameters.yaml:8`, p.ex. `celesta-prod-2-valkey.prod-2.octopoprod.com`). Checar antes de premiar, dentro desses locks, é seguro contra corrida. Dispensa unique, desnormalização, e o problema do EntityManager fechado pela violação dentro do `try`.
- Fora do escopo, anotado pelo Opus: com a guarda, o redelivery ainda grava um segundo `promotion_event` pelo `Record`. Não paga nada; só importa se algo ler esses eventos para decidir reward, o que não foi verificado.
- Desenho para o plano, bonus model: a marca vai no flush de `updateStatusesAndCounters:118`, depois da chamada HTTP à wallet, como o status já vai hoje. A janela "wallet respondeu, flush caiu" continua existindo, igual a hoje. O spec nomeia essa janela como limitação conhecida, em vez de deixar implícito.
