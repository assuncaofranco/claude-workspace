# CLS-4742 — matriz

2026-11-16. Lida do `origin/master` de promotion (`94cd950b4`), backoffice-front (`c5e190c6e`), scenario
(`e7ca165`) e constants. Escopo desta conversa: 4828 (promotion) e 4830 (front). Scenario (4827) e
backoffice (4829) estão com o Charles: entram só onde o contrato cruza, sem plano nosso.

**Status:** aguardando sign-off do Lucas na classificação. Where e Proof vazios até o implement.

## Dimensões

| # | Dimensão | Valores | Fonte |
|---|---|---|---|
| D1 | Tipo da configuração | free, deposit, free_rounds, gift | `celesta-constants` `RewardConfigurationConstants::TYPES` |
| D2 | Página de detalhe no front | `reward-model/index.js` (free, deposit, free_rounds); `GiftConfiguration.js` (gift) | `reward-model/index.js:89` `if (type === BONUS_TYPE_GIFT) return <GiftConfiguration />` |
| D3 | Tipo da promoção | deposit_tier, first_bet_insurance, refer_friend, instant_reward, multiplus | `PromotionConfigurationConstants::TYPES` |
| D4 | Onde a recompensa fica na promoção | aggregator tier, bet_result, raf_role (referrer, referee), multiplus_tier; instant reward lê também `reward` direto da promoção | `RewardAggregatorConstants::TYPES`, `RAF_ROLES`; `InstantReward/Handler/RewardHandler.php` `findBy(['promotionConfiguration' => …])` |
| D5 | Multiplicidade | 0; 1; várias linhas na mesma promoção (bandas, papéis); várias promoções | `Reward` ManyToOne; `RewardAggregator::$rewards` |
| D6 | Status da promoção | enabled, disabled | `PromotionConfigurationConstants::STATUSES`; filtro `status` é opcional (`PromotionConfigurationRepository.php:233`) |
| D7 | Coluna que guarda a referência | `reward.reward_configuration_id`; legado só `bonus_model_id` | `Reward.php:41-47`; `RewardSubscriber.php` grava as duas desde que o form resolve `bonusModelId` para configuração |
| D8 | Domínio | mesmo da configuração; outro | lista é por `pc.domainId` (`PromotionConfigurationRepository.php:63`); scenario idem pelo path |
| D9 | Endpoint da promotion | lista `POST …/promotion-configurations`; count `…/count` | os dois chamam `applyPromotionConfigurationFilters` (`:68`, `:121`); count é `COUNT(pc.id)` |
| D10 | Variante do `offer_reward` no scenario | opções de bônus; opções de gift | `OfferBonusOptionsType` e `OfferGiftOptionsType`, as duas com `rewardConfigurationId` |
| D11 | Papel do usuário do BO | com e sem `ROLE_PROMOTIONS`; com e sem `ROLE_SCENARIO` | `SegmentLinkedAssets.js`, linha só renderiza com `policies?.[ROLE_…]` |
| D12 | Resultado da busca | itens; vazio; erro | `SegmentLinkedAssets.js` `.then` / `.catch(() => data: [])` |
| D13 | Link da linha | lista filtrada por hash | `SegmentLinkedAssets.js` `href=…/promotions?#segmentIds=`; `useSearchBar.js:35` descarta chave que não está no `filterConfig` |

Fora como dimensão: `offeringMethod` (o card não ramifica por ele), paginação (front pede `limit: 1000`,
nenhum caso real chega perto).

## Casos

### Promotion (4828)

| # | Célula | Classe | Justificativa | Critério | Where | Proof |
|---|---|---|---|---|---|---|
| P1 | deposit_tier, config X em uma banda | A | — | given deposit tier com X numa banda, when lista filtrada por `rewardConfigurationIds=[X]`, then a promoção aparece uma vez | | |
| P2 | deposit_tier, X em duas bandas | A | — | given X em duas bandas da mesma promoção, when lista filtrada por X, then a promoção aparece uma vez | | |
| P3 | first_bet_insurance, X em `bet_result` | E → P1 | `FirstBetInsurance/Form/Type/RewardAggregatorType` estende o Standard sem sobrescrever `buildForm`, que registra `RewardAggregatorSubscriber` (`:31` grava `promotion_configuration_id` em cada reward). Reward avulsa em aggregator: `RewardController::postRewardForAggregator():295` idem | — | | |
| P4 | multiplus, X em `multiplus_tier` | E → P1 | `Multiplus/Form/Type/RewardAggregatorType`, mesma herança de P3 | — | | |
| P5 | refer_friend, X só no referee | A | spec pede explícito; mesma herança de P3, mas é o caso que a spec nomeia | given refer a friend com X só na lista do referee, when lista filtrada por X, then a promoção aparece | | |
| P6 | refer_friend, X no referrer e no referee | E → P2 | duas linhas `reward` da mesma promoção, aggregators `raf_role` distintos | — | | |
| P7 | instant_reward com X | A | reward sem aggregator, criada por `RewardController::postReward():127` com a promoção no contexto. Mesmo `promotion_configuration_id`, mas é a célula que quebra se o filtro for escrito passando por `rewardAggregators` | given instant reward com X, when lista filtrada por X, then a promoção aparece | | |
| P8 | X em 2 promoções, Y numa terceira | A | — | given promoções A e B com X e C com Y, when lista filtrada por X, then só A e B | | |
| P9 | nenhuma promoção com X | A | — | given nenhuma promoção usa X, when lista filtrada por X, then lista vazia | | |
| P10 | promoção disabled com X | A | o card não passa `status`, como o de segmento; a lista devolve os dois status | given promoção disabled com X, when lista filtrada só por X, then a promoção aparece | | |
| P11 | outra promoção de outro domínio com X | N | X pertence a um domínio; `RewardSubscriber` resolve a configuração por `getDomainId()` da promoção, então outro domínio não consegue referenciar X | — | | |
| P12 | count filtrado por X, X em duas bandas | A | `COUNT(pc.id)` com JOIN conta linhas de `reward`, não promoções | given X em duas bandas, when count filtrado por X, then `1` | | |
| P13 | reward trocada de X para Y | A | edição é por `PATCH …/reward/{id}` (`RewardController.php:162`), que passa por `RewardSubscriber` e regrava `reward_configuration_id`. O filtro lê a linha na hora, sem cópia | given reward trocada de X para Y, when lista filtrada por X, then a promoção some; filtrada por Y, aparece | | |
| P13b | reward com X apagada | E → P13 | `DELETE …/reward/{id}` é remoção real (`RewardRepository::delete()` `$em->remove`); aggregator apagado leva as rewards (`cascade remove`, `orphanRemoval`) | — | | |
| P14 | recompensa legada só com `bonus_model_id = X` | A | `reward_configuration_id` nasceu em `Version20260709093215` sem backfill: a migration B do CLS-1604 (`UPDATE reward SET reward_configuration_id = bonus_model_id`) foi apagada em `3fbf4b0fa`, e não há backfill no celesta-scripts. O código já trata as duas como o mesmo id: `Reward::getRewardSourceId()` = `rewardConfiguration?->getId() ?? bonusModelId` (ids preservados pelo CLS-1142). O filtro segue essa régua. Preprod diz quantas linhas há, não se o caso existe em prod | given reward com `reward_configuration_id` NULL e `bonus_model_id` = X, when lista filtrada por X, then a promoção aparece | | |
| P15 | config gift em promoção | N | `RewardSubscriber.php` recusa gift como recompensa de promoção; gift de promoção é do CLS-3916 | — | | |
| P16 | filtro vazio `rewardConfigurationIds: []` | A | o BO repassa com `?? []` (padrão do `segmentIds`); vazio não pode filtrar nada | given filtro vazio, when lista, then mesmo resultado de hoje | | |

### Front (4830)

| # | Célula | Classe | Justificativa | Critério | Where | Proof |
|---|---|---|---|---|---|---|
| F1 | free, 2 cenários e 1 promoção | A | — | given config free usada por 2 cenários e 1 promoção, when abre o detalhe, then card com 2 e 1, tooltip `#id \| nome` | | |
| F2 | deposit | E → F1 | mesma página `index.js` | — | | |
| F3 | free_rounds | E → F1 | mesma página `index.js` | — | | |
| F4 | gift | A | outra página, `GiftConfiguration.js`; linha de promoções sempre 0 (P15) | given config gift usada por um cenário, when abre o detalhe, then card com cenários 1 e promoções 0 | | |
| F5 | sem uso | A | — | given config sem uso, when abre o detalhe, then 0 nas duas linhas, sem link | | |
| F6 | usuário sem `ROLE_PROMOTIONS` | A | esconde a linha, como `SegmentLinkedAssets.js` (`policies?.[ROLE_PROMOTIONS] &&`). Decisão do Lucas, 2026-11-16: o padrão existente é a régua | given usuário sem `ROLE_PROMOTIONS`, when abre o detalhe, then a linha de promoções não aparece e a de cenários sim | | |
| F7 | usuário sem `ROLE_SCENARIO` | E → F6 | mesma regra | — | | |
| F8 | busca falha | A | spec pede mensagem; segmento mostra 0. Pergunta 2 ao PO é só se o segmento muda junto (OUT diz que não) | given a lista de promoções responde erro, when abre o detalhe, then a linha mostra erro e o resto da página carrega | | |
| F9 | clique no número | A | `useSearchBar` descarta chave fora do `filterConfig`: sem `rewardConfigurationIds` em `fcPromotions` e `fcScenarios`, o link abre a lista sem filtro. **Não está na todo list da 4830** | given card com 1 promoção, when clica no número, then a lista de promoções abre filtrada por X e mostra só ela | | |
| F10 | config editada depois em outra aba | E → F1 | o card busca no mount (`useEffect`), sem cache | — | | |
| F11 | 6 locales | A | spec | given cada locale, then os rótulos novos existem | | |

### Contrato entre repositórios (só ordem, nada a planejar aqui)

| # | Célula | Classe | Justificativa |
|---|---|---|---|
| C1 | BO novo repassa a chave antes da promotion nova | A (deploy) | form da promotion não tem `allow_extra_fields`: campo desconhecido vira 400 na lista inteira. Ordem promotion e scenario → backoffice → front, nas instruções de deploy |
| C2 | scenario, gift e bônus | E | as duas variantes usam `rewardConfigurationId` (D10). É da 4827, do Charles: só registrar para o review da story |

## Pendências antes do rascunho dos planos

1. P14 medido em preprod-1, 2026-11-16: 70 rewards, 67 com `reward_configuration_id` (todas iguais ao `bonus_model_id`), **0 só com `bonus_model_id`**, 3 sem nenhuma das duas. O backfill rodou em pp1 por fora do código, ou todas as linhas são posteriores a julho. Prod não dá para ler, e nem o CLS-1604 nem o CLS-1605 registram backfill no Jira: a classe A fica, e o filtro segue `getRewardSourceId()`.
2. F8: pergunta 2 do `understand/evaluate-CLS-4742.md` sem resposta; a classe vale com o OUT da spec (segmento não muda). F6/F7 decididos.
3. F9 entra no plano da 4830 como tarefa (cabe no AC "links match the segment card", não muda spec).
4. 4827 está Planned sem branch nem PR no scenario: perguntar ao Charles onde está o plano.
