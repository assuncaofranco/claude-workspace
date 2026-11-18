# CLS-3865 — matriz

Enumerada em 2026-11-16, do código em `origin/*` (fetch do mesmo dia). Classes são **proposta**: a
classificação é do Lucas. `?` = sem classe até o PO responder se há gift em produção.

Siglas de repositório: **C** constants · **P** promotion · **S** statistics · **BI** terraform-bi ·
**BO** backoffice · **J** job-library · **ACT** activity · **F** backoffice-front.

## Dimensões

| # | Dimensão | Valores | Fonte |
|---|---|---|---|
| D1 | Status do gift antes da ação | claimed, canceled, completed (novo) | C `GiftConstants.php:7-8,17-22` @CLS-4434; completed pela 4935 |
| D2 | Ação | editar valor, concluir, cancelar, listar | spec; cancel = `PATCH …/gift/{id}` `{status}` P `GiftController.php:214-228` @CLS-4434 |
| D3 | Origem do gift | oferta direta no BO, scenario, request aprovado, prêmio de promoção (3916), anterior ao release | P `GiftFactory.php:31,47`; `GiftRequestManager.php:91` @CLS-4540; `RewardSubscriber.php:98-99` (hoje recusa) |
| D4 | Estado da configuração | enabled, disabled, soft-deleted, nula | C `RewardConfigurationConstants.php:31-32`; P `RewardConfiguration.php:52,59,62`; `Gift.php:78-80` (FK nullable) |
| D5 | Valor na edição | 0, negativo, 0.01, 2 casas, 3 casas, 8 dígitos inteiros, 9 dígitos, não numérico, igual ao atual | regra do offer: P `Model/Request/Gift.php:80-82` @CLS-4434 (`GreaterThan(0)`, `/^\d{1,8}(\.\d{1,2})?$/`) |
| D6 | Concorrência (par de ações no mesmo gift) | concluir×concluir, concluir×editar, editar×editar, concluir×cancelar, editar×cancelar | P `GiftService.php:29` transação + `GiftRepository.php:120-130` `PESSIMISTIC_WRITE` @CLS-4434 |
| D7 | Mensagem para a statistics | created(claimed), status_changed→completed, status_changed→canceled, reentrega, edição de valor | P `GiftEventSubscriber.php:32-45`; S `GiftEventBatchItem.php:41-61` |
| D8 | Período | criação e conclusão no mesmo dia, em dias diferentes | S `GiftEventBatchItem.php:44,57` (`date` = dia de `statusChangedAt`); BI `player_kpi.tf:253-263` (`date(created_at)`) |
| D9 | Consumidor do KPI | statistics diário, statistics total, generosity, BI player_kpi (3 jobs), BI player_kpi_sum | S `KpiWriter.php:36,38`; `Version20261407000002.php:20`; BI `player_kpi.tf:65-80,337-352,609-624`; `player_kpi_sum.tf:116-124` |
| D10 | Permissões do usuário | nenhuma, só View (`PS_GIFT_LIST`), Edit (`PS_GIFT_OFFER`), Cancel (`PS_GIFT_CANCEL`), só `PS_GIFT_REQUEST`, só `PS_GIFT_REQUEST_VALIDATE` | BO `Version20260922000000.php:15-16`; `Version20261109000000.php:12-17` @CLS-4437 e @CLS-3094-CLS-4542 |
| D11 | Superfície | aba Gifts do player, página Gifts to order | spec |
| D12 | Domínio | do usuário, outro domínio | P `GiftRepository.php:183-188`; BO `DomainSubscriber.php:55-69` |
| D13 | Locale | en, es, fr, hi, pt, zh | F `src/translations/{en,es,fr,hi,pt,zh}.js` |

D3 "anterior ao release" e D4 "nula" se cruzam: gift criado antes de `Version20261109144816` tem
`reward_configuration_id` nulo. A migration `Version20261029170000` apagou todos os gifts, então só
os criados entre 2026-10-29 e o deploy da 20261109 estão nesse caso — se existirem em produção.

## Casos

Where e Proof vazios até a implementação.

### Promotion — transições e edição (4935, 4941)

| # | Célula | Classe | Justificativa | Critério | Where | Proof |
|---|---|---|---|---|---|---|
| 1 | concluir × claimed | A | — | given a claimed gift, when PATCH status `completed`, then 200 and GET returns `status = completed` | | |
| 2 | concluir × completed | A | — | then 400 "Impossible to change status from completed to completed", gift unchanged | | |
| 3 | concluir × canceled | A | — | then 400, gift stays `canceled` | | |
| 4 | cancelar × completed | A | status novo; a rejeição vem do mapa de transições da 4434 (`canceled` só de `claimed`), sem código novo | then 400, gift stays `completed` | | |
| 5 | cancelar × claimed | N | comportamento do CLS-3508, inalterado | — | | |
| 6 | editar × claimed, valor válido | A | — | given a claimed gift of 100.00 EUR, when edit value 80.50, then 200, `amount = 80.50`, `currency = EUR` | | |
| 7 | editar × completed | A | — | then 400, `amount` unchanged | | |
| 8 | editar × canceled | A | — | then 400, `amount` unchanged | | |
| 9 | editar com `currency` no body | A | — | then currency unchanged (ignored or 400, a decidir no plano) | | |

### Valor na edição (4941, 4943)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 10 | 0 | A | limite inferior | 400, nothing saved |
| 11 | negativo | E → 10 | mesmo `GreaterThan(0)` (`Gift.php:81`) | — |
| 12 | 0.01 | A | menor válido | 200 |
| 13 | 3 casas | A | — | 400 |
| 14 | 9 dígitos inteiros | A | o regex do offer limita a 8; a spec não fala de máximo | 400 |
| 15 | não numérico / vazio | A | — | 400 |
| 16 | igual ao atual | **sem proposta** | a spec não diz. Aceitar grava um `gift_value_edited` com old = new | — |

### Configuração (4941)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 17 | disabled × editar/concluir/cancelar | A | o offer recusa config não enabled (`GiftRewardConfigurationConstraintValidator.php:37-42`); o endpoint novo não pode herdar | 200 nas três |
| 18 | soft-deleted × editar/concluir/cancelar | A | filtro global de soft delete (`doctrine.yaml:35-37`): proxy da config apagada pode quebrar na serialização. O cancel já passa nesse caso (`bo_user_cancels_gift.feature:30-45`) | 200 nas três |
| 19 | config nula | ? | só existe se houver gift anterior a 2026-11-09 em produção | — |

### Origem e colunas da lista (4940, 4944)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
Spec de 2026-11-17 12:05 UTC: colunas status, gift ID, gift name, value, currency, player ID, offered by,
offered at, approved by, approved at. Saíram reason, created by/at e requested by. A escolha de coluna é
do front; o endpoint devolve os campos que já existem.

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 20 | oferta direta | A | — | approved by / approved at = "—"; offered by = BO user |
| 21 | request aprovado | A | — | approved by, approved at filled. Nota: `source_user_id` = aprovador (`GiftFactory.php:47`), então offered by = approved by |
| 22 | scenario | A | decisão 4: mostra a origem | offered by = the scenario, not "—" |
| 23 | prêmio de promoção (3916) | A | a 4770 (3916) troca a origem por `Source`; a 4773 foi cancelada. Offered by depende da 4770 estar no master | approved = "—"; offered by = the promotion |
| 24 | anterior ao release | N | decisão 1: sem regra especial | — |

### Lista do domínio (4940, 4942, 4944)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 25 | claimed, canceled e completed misturados, filtro `claimed` (aba To order) | A | — | only claimed returned, oldest first |
| 25b | idem, filtro `completed` (aba Ordered, nova na spec de 17/11) | A | — | only completed returned, oldest first |
| 25c | gift concluído | A | — | leaves the `claimed` result and shows in the `completed` result |
| 25d | gift cancelado | A | — | in neither result; still in the player Gifts tab |
| 26 | gift de outro domínio | N | filtro `g.domainId` já existe (`GiftRepository.php:183-188`) | — |
| 27 | filtro de moeda com e sem match | A | — | only that currency / empty |
| 28 | zero gifts no status filtrado | A | — | empty state, per tab |
| 29 | mais de 100 | A | decisão 5: pagina com o `limit`/`offset` que a lista já aceita | second page returns the rest, same order |

### Concorrência (4941)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 30 | concluir × concluir | A | lock + máquina de estados: o segundo vê `completed` | one 200, one 400 |
| 31 | concluir × editar | A | idem; se a edição vem antes, o `completed` leva o valor novo | first wins, second 400 |
| 32 | editar × editar | A | **o lock não dá erro aqui**: as duas edições passam em série e a segunda sobrescreve. "Second gets an error" exige o valor esperado (ou uma versão) na requisição | second 400/409 |
| 33 | concluir × cancelar | E → 30 | mesma trava, mesma máquina de estados (`GiftService.php:29-46`) | — |
| 34 | editar × cancelar | E → 31 | idem | — |

### Statistics (4938)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 35 | created(claimed) depois do release | A | hoje conta (`kpi.yaml:279-287`) | counts nowhere |
| 36 | status_changed → completed | A | hoje é descartado: `PRIMARY KEY (gift_id)` (`Version20261407000003.php:39`) + `ON DUPLICATE KEY UPDATE gift_id = gift_id` (`EventBatchProcessor.php:88-90`) | counts once, at the event amount, on the completion day |
| 37 | status_changed → canceled | A | — | counts nowhere |
| 38 | reentrega do completed | A | — | still counts once |
| 39 | edição de valor | N | o subscriber só emite com status no changeset (`GiftEventSubscriber.php:36-38`) | — (a promotion não manda nada; conferir no teste da 4941) |
| 40 | criado em D1, concluído em D2 | A | `date` = dia de `statusChangedAt` | counts on D2, not D1 |
| 41 | total (`kpi_wallet_sum`) | E → 36 | mesmo `KpiWriter.php:252-296` | — |
| 42 | generosity | E → 36 | fórmula lê `giftClaimedAmount` (`Version20261407000002.php:20`); muda junto se a 4938 mantiver o nome | — |
| 43 | moedas diferentes | N | agregado por moeda, sem conversão (`KpiBatchAggregator.php:34`), inalterado | — |
| 44 | anterior ao release, concluído depois | ? | já contou na criação; contradiz o texto da 4938 | — |
| 45 | anterior ao release, cancelado depois | ? | — | — |
| 46 | `kpi:reconsolidate` sobre período anterior | ? | reconstrói a partir de `event_promotion` com a regra nova: um created/claimed antigo deixa de contar e o passado muda (`KpiReconsolidateProcessor.php:110-176`). Só eventos de 14 dias ficam (`KpiEventsCleanupCommand.php:30`) | — |

### BI (4939)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 47 | completed | A | — | counted on `date(updated_at)` |
| 48 | claimed / canceled | A | — | not counted |
| 49 | player_kpi_sum | E → 47 | rebuild diário de player_kpi (`player_kpi_sum.tf:63-64,116-124`) | — |
| 50 | anterior ao release, primeiro `player_kpi_eow` depois do deploy | ? | o job apaga e reescreve 7 dias (`player_kpi.tf:609-626`): gift claimed criado nesses 7 dias **some** de partição anterior ao release, o que quebra o "past periods unchanged" | — |

### Permissões e proxies (4942)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 51 | Edit gifts | A | — | edit and complete 200 |
| 52 | só View gifts | A | — | list 200; edit/complete 403 |
| 53 | nenhuma | A | — | list 403 |
| 54 | só `PS_GIFT_REQUEST` | A | o offer aceita OFFER **ou** REQUEST (`GiftController.php:77-81` @CLS-3094-CLS-4542); edit/complete não podem herdar | edit/complete 403 |
| 55 | só `PS_GIFT_REQUEST_VALIDATE` | **sem proposta** | o validador de requests não vê Gifts to order; é intenção? | — |
| 56 | cancel na Gifts to order com Cancel gift | E → CLS-3508 | mesma rota `promotion_gift_cancel` | — |
| 57 | rejeições da promotion (valor, status, concorrência) | A | `FormHelper::handleV2Exception` vira 400 genérico; o 409 só passa no `GiftRequestErrorTrait` | the front shows the promotion's message |
| 58 | evento só no sucesso | A | padrão do cancel (`UserActivityJobManager.php:202-212`) | one `gift_value_edited` / `gift_completed` per success, none on failure |
| 59 | grants dos roles | N | chaves técnicas não mudam; `role_policy` intocado | — |

### Front (4943, 4944)

| # | Célula | Classe | Justificativa | Critério |
|---|---|---|---|---|
| 60 | claimed + Edit gifts, nas duas superfícies | A | — | Edit value and Complete shown |
| 61 | completed | A | — | label "Completed", no action |
| 62 | canceled | E → CLS-3508 | — | — |
| 63 | só View gifts | A | — | no action |
| 64 | Complete confirmar / desistir | A | — | confirm → completed; dismiss → nothing |
| 65 | labels de permissão | A | os labels que a tela mostra estão no **front** (`en.js:153,177`: "Execute Offer gift", "Access Gifts tab"); no BO só existe `Give gift` (`messages.en.yml:1734`). A 4942 manda relabel no BO; a 4943/4944 não mencionam | "View gifts" / "Edit gifts" in the 6 locales |
| 66 | descrição do Generosity | A | `en.js:4015` | says completed gifts |
| 67 | filtros e descrição dos eventos novos no player Logs | A | listas em `logs.js:79,137` e `variables/index.js:392`; o filtro do BO vem sozinho de `UserActivityJob::EVENTS` | both events filterable and described |
| 68 | locales | A em en, E nos outros 5 | mesmo `translations-check.js` | — |

## Achados que mudam o plano (não são células)

1. **A 4940 quase existe.** `GET /domain/{domainId}/gifts` já filtra status e moeda e ordena por
   `createdAt` (P `GiftController.php:242` @CLS-4434, `FilterType.php:32-58`, `QueryType.php:14-25`);
   a CLS-4540 já põe requester/approver na resposta. No BO também já há `GET /gifts` de domínio
   (`GiftConfigurationController.php:155`).
2. **Concluir pode ser só uma transição nova no `PATCH` do cancel**, sem endpoint novo.
3. **A CLS-4545 (front, Dimitris, Implemented) já tem uma página "Gift checkout"**, com Edit value,
   Complete, Cancel e **Adjustment**, menu `side_menu.gift_checkout` gated por `ROLE_PLAYERS_GIFTS_TAB`,
   chamando `POST /gift/{id}/complete`, `PATCH /gift/{id}` e `POST /gift/{id}/adjustment` — rotas que
   não existem no BO (F `giftCheckout.ts:44-65`, `GiftCheckoutListItem.tsx:28-32`). A 4943 e a 4944
   partem dessa branch: ou o contrato da 4942 segue essas rotas, ou o front muda. Adjustment não
   está em escopo nenhum.
4. **`offered` existe no front**, não no back: label em `en.js:1907-1911` (master) e o Cancel da
   CLS-4438 aparece para `offered` ou `claimed`. Isso explica o `offered` da spec; a pergunta 2 ao PO
   vira só confirmação. Também: master chama `completed` de "Delivered", a CLS-4438 de "Completed".
5. **Colisão de migration no BO**: CLS-4437 e CLS-3094-CLS-4542 criam ambas
   `Version20261109000000`. A 4942 parte das duas.
6. **Created by** não é coluna: é `source_user_id`. Nulo em gift de scenario (#22) e, depois da
   4773, sai de vez (#23).
