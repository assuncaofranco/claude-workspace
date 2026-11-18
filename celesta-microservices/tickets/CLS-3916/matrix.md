# CLS-3916 — matriz

Enumerada em 2026-11-16 do `origin/master` de promotion (`94cd950b4`), constants (`0623f926`),
job-library (`a52cf8a`), activity (`e85d3d64`) e backoffice (`5a119bde5f`). Neste ticket, a classificação
é minha: o Lucas delegou em 2026-11-16 ("é você quem lê"). Os casos marcados "?" ficam com o PO (comentário
92818 no CLS-3916). Where e Proof ficam vazios até o implement.

## Dimensões

| # | Dimensão | Valores | Fonte |
|---|---|---|---|
| D1 | Tipo de promoção | deposit_tier, first_bet_insurance, refer_friend, instant_reward, multiplus | constants `PromotionConfigurationConstants::TYPES:29-35` |
| D2 | Papel no RAF | referrer, referee | promotion `ReferAFriend/Handler/RewardHandler.php:123-143` |
| D3 | Tipo do item de prêmio | future_deposit, free_bonus, free_round, match_deposit, match_bet, **gift (novo)** | constants `RewardConstants::TYPES:13-19`; por tipo de promoção em `PromotionConfigurationBundle/*/Form/Type/RewardType.php::getAllowedTypes()` |
| D4 | Tipo da config referenciada | free, deposit, free_rounds, gift | constants `RewardConfigurationConstants::TYPES:7-12`; hoje gift recusado em `RewardSubscriber.php:98-101` |
| D5 | Estado da config no save | enabled, disabled, soft-deleted, outra moeda, outro domínio | `RewardConfigurationConstants::STATUSES:31-33`; `RewardConfiguration.php:59` (SoftDeleteable); domínio em `RewardConfigurationRepository::getRewardConfiguration():52` |
| D6 | Estado da config na premiação | enabled, disabled, soft-deleted | idem D5; FK `reward.reward_configuration_id` `onDelete: SET NULL` (`Reward.php:45`); `RewardHandler.php:221` pula config null em silêncio |
| D7 | Estoque da config | null (sem limite), abaixo, atingido | `RewardConfiguration.php:99`; `GiftRepository::saveWithinStock():46-66` |
| D8 | Offering status da config | active, inactive | `RewardConfigurationConstants::OFFERING_STATUSES:45-47` — spec não fala |
| D9 | Composição da faixa/regra | só gift, gift + bônus, dois gifts, só bônus | `RewardAggregatorService::getRewardsByPromotionConfiguration` → loop `RewardHandler.php:216` |
| D10 | Moeda do jogador | wallet na moeda da promoção, só outra moeda, sem moeda | `RewardHandler.php:207` (sem moeda → return antes do loop); `BonusCurrencyGuard.php:36` |
| D11 | `bonus_offer_allowed` | true, false | `Validator/Reward/BonusOfferAllowedValidator.php:27` (todos exceto RAF, `validators.yml:130-140`); RAF `RewardHandler.php:121,134,241` |
| D12 | Processamento | primeiro, reprocesso após falha da wallet, evento concorrente | `RewardHandler.php:239-247` (V2Exception → relança, não flusha); lock `acquireConfigLock():256-286`; RAF flusha por papel `:252-253` e engole exceção `:152` |
| D13 | Motivo da config | com `reason_id`, sem, motivo apagado | `Gift.php:72-74`; config ganha `offeringReason` no CLS-4743 (plano, ainda não no master) |
| D14 | Origem do gift existente (backfill) | user, scenario, nenhuma | `Gift.php:81-86`; replay SQL `GiftController.php:325-326` |
| D15 | Leitor da config de promoção | rota do jogador, rota do BO, potential winnings | `PromotionConfigurationController.php:76,91` (BO) e `:115,131` (jogador); `PotentialWinningsCalculator.php:150-162` (`default => null`) |
| D16 | Status do gift depois | claimed, (completed, canceled) | constants `GiftConstants::STATUSES:9-11` = só `claimed`; os outros vêm do CLS-3865 |
| D17 | Activity | `gift_offered` source `promotion` | job-library `UserActivityJob::SOURCE_TYPES:109-118` (sem promotion); BO `Log/FilterType.php:27,52` lê a mesma lista; activity `AllSourceTypes` |
| D18 | Idioma | 6 locales | front / BO |

## Casos

| # | Célula | Classe | Justificativa | Critério | Where | Proof |
|---|---|---|---|---|---|---|
| 1 | gift × deposit_tier | A | — | dada uma deposit tier com uma faixa cujo prêmio é gift (config X), quando o jogador deposita na faixa, então `GET /gifts?filter[playerId]` traz 1 gift `claimed` com nome, valor e moeda de X e origem = a promoção | | |
| 2 | gift × first_bet_insurance | A | handler próprio, `FirstBetInsurance/Handler/RewardHandler.php:55` | idem 1, disparado pela aposta perdida | | |
| 3 | gift × instant_reward | A | handler próprio, `InstantReward/Handler/RewardHandler.php:51` | idem 1, disparado pelo evento da regra | | |
| 4 | gift × refer_friend × referrer | A | caminho próprio, `ReferAFriend/Handler/RewardHandler.php:275` com `recipientPlayerId` | gift no player do **referrer**, origem = a promoção | | |
| 5 | gift × refer_friend × referee | A | idem, papel referee | gift no player do **referee** | | |
| 6 | gift × multiplus | A | `Multiplus/Form/Type/RewardType.php:40` só aceita free_bonus | save com `type: gift` numa multiplus → 400 em `type` | | |
| 7 | type=gift × config gift enabled, mesma moeda e domínio | A | — | save → 200, o GET da promoção devolve o item com `type: gift` e `rewardConfigurationId` | | |
| 8 | type=gift × config **não** gift (free/deposit/free_rounds) | A | hoje o subscriber só olha a config, não o par | save → 400 em `rewardConfigurationId` | | |
| 9 | type de bônus × config gift | A | hoje recusado em `RewardSubscriber.php:98`; tem de continuar | save → 400, mensagem atual | | |
| 10 | config gift disabled no save | A | — | 400 em `rewardConfigurationId` | | |
| 11 | config gift soft-deleted no save | A | `getRewardConfiguration` com filtro de soft-delete ligado → null | 400 "does not exist" | | |
| 12 | config gift em outra moeda | A | não existe checagem de moeda hoje para bônus | 400 em `rewardConfigurationId` | | |
| 13 | config gift de outro domínio | E → 11 | mesmo `getRewardConfiguration():52` filtra domínio → null | — | | |
| 14 | só gift na faixa | A | — | 1 gift, nenhum bônus, instância `rewarded` | | |
| 15 | gift + bônus na faixa | A | — | 1 gift + 1 bônus, instância `rewarded` | | |
| 16 | dois gifts na mesma faixa | A | "one gift per reward" | 2 gifts | | |
| 17 | só bônus (regressão) | A | o loop `RewardHandler.php:216` muda | bônus como hoje, nenhum gift | | |
| 18 | jogador sem moeda | A | `RewardHandler.php:207` retorna antes do loop; a spec manda criar o gift | gift criado na moeda da promoção; bônus pulado como hoje | | |
| 19 | jogador só com wallet em outra moeda | A | bônus: `BonusCurrencyGuard` lança e é logado `:234` | gift criado na moeda da promoção; bônus falha como hoje | | |
| 20 | estoque atingido | A | `saveWithinStock()` devolve null quando atinge | gift criado mesmo assim e entra na contagem | | |
| 21 | estoque null / abaixo | E → 1 | `saveWithinStock():49` | — | | |
| 22 | config disabled na premiação | A | — | gift pulado, bônus da faixa saem, instância `rewarded`, log com o motivo | | |
| 23 | config soft-deleted na premiação | A | proxy de entidade soft-deleted com filtro ligado lança ao carregar (mesmo problema que o plano do CLS-4743 descreve) | idem 22, **sem exceção** | | |
| 24 | reprocesso depois de falha da wallet no bônus da mesma faixa | A | `:239-247` relança e não flusha; o evento volta | um gift só, nunca dois | | |
| 25 | RAF: referrer premiado, referee falha | A | flush por papel `:252-253`, catch-all `:152` | reprocesso não duplica o gift do referrer | | |
| 26 | `bonus_offer_allowed = false` | **?** | o validator barra a premiação inteira (`BonusOfferAllowedValidator.php:27`), então hoje nem bônus nem gift. A spec diz "player status doesn't block, as for promotion bonuses" — bônus de promoção **são** barrados por isso | **pergunta ao PO** | | |
| 27 | offering status inactive da config gift | **?** | a spec não fala; bônus de promoção hoje não checam | **pergunta ao PO** | | |
| 28 | motivo: config com `reason_id` | A | depende do CLS-4743 | `reasonId`/`reasonName` do gift = os da config | | |
| 29 | motivo: config sem motivo | A | — | `reasonId: null` | | |
| 30 | motivo apagado depois de configurado | A | motivos são soft-deleted, `Gift.php:72` sem filtro na leitura | gift guarda o id do motivo apagado | | |
| 31 | editar a config depois da premiação | A | gift copia nome/valor/moeda (`GiftFactory`) | gift já criado não muda | | |
| 32 | backfill: gift de user | A | só se ficar a entidade `Source` (4770) | API devolve `sourceUserId` igual a antes | | |
| 33 | backfill: gift de scenario | A | idem | `sourceScenarioId` igual a antes | | |
| 34 | replay de idempotência depois do drop (4773) | A | SQL cru `GiftController.php:325-326` | replay continua devolvendo a origem | | |
| 35 | rota do jogador | A | — | `GET /player/{id}/promotion-configurations` não traz item gift; faixa só com gift aparece sem prêmio | | |
| 36 | rota do BO | A | — | traz o item gift | | |
| 37 | potential winnings | N | `PotentialWinningsCalculator.php:161` `default => null` ignora tipos desconhecidos | — | | |
| 38 | `RewardAmountCalculator` com gift | A | `RewardAmountCalculator.php:23` lança `InvalidArgumentException` para tipo desconhecido, e `RewardHandler.php:234` não pega: **a premiação inteira falha**. Se o 4771 for antes do 4772, uma faixa com gift perde também os bônus | 4771 e 4772 no mesmo deploy, ou o 4771 sem o save liberado | | |
| 39 | `gift_offered` com source promotion | A | — | 1 evento por gift, `source_type: promotion`, `source_user_id` = id da promoção; nenhum `gift_claimed` | | |
| 40 | filtro de logs do BO por `sourceTypes: [promotion]` | A | BO valida contra `UserActivityJob::SOURCE_TYPES` (`FilterType.php:52`): precisa do pin novo da job-library no BO | 200 com os eventos | | |
| 41 | statistics: criação e mudança de status | E → 1 | `GiftEventSubscriber` emite em todo persist e mudança de `status`, sem olhar a origem (`:32-45`) | — | | |
| 42 | editar / completar / cancelar gift de promoção | **?** | `GiftConstants::STATUSES` só tem `claimed`; isso é do CLS-3865 | **pergunta ao PO** (já na lista) | | |
| 43 | limites de premiação | E → 17 | `updateStatusesAndCounters():97-127` roda depois de `processReward` e não olha o tipo do item | — | | |
| 44 | locales | A | — | 6 locales com as labels novas | | |

## Achados para o pai (não planejar em cima)

- **38** é ordem de deploy, não pergunta: entra no release do 4771/4772.
- **26, 27, 42** vão ao PO junto com as três de readiness (motivo já resolvido pelo 4743: copia o `reasonId` da config).
- **23** e **25** viram critério explícito no plano do 4772.
