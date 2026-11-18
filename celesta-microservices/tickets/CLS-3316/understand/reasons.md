# CLS-3316 — que motivos existem

Lido do origin/master em 2026-11-16. O que existe de fato nos dados ainda não foi consultado.

## Hoje

| Onde | Forma | Valores | Prova |
|---|---|---|---|
| configuração (bônus) | lista fixa no código, igual para todas as marcas | 31 chaves | `celesta-constants` `RewardConfigurationConstants.php:71-101`; validado por `Assert\Choice` em `promotion` `ApiBundle/Model/Request/RewardConfiguration.php:282` |
| front, rótulos da configuração | tradução por chave | as 31 + 10 antigas marcadas `[EXPIRED]`/`[OBSERVED]` | `backoffice-front` `src/translations/en.js`, `reward.form.reason.*` |
| gift | lista por marca (`reward_offering_reason`) | seed: Birthday, Christmas, Easter, Valentine's day | `tickets/CLS-3282/CLS-4163/seed-reasons.sql` |

As 31 chaves: loyalty_vip, sign_up, registration, 1st_deposit, 2nd_deposit, 3rd_deposit,
4th_deposit, enhanced_wo, x_sell_lc, x_sell_slots, tournaments, network_campaigns, shop_item,
shop_cash, dfg, raf, vip_promotion, promotions, onsite_promotions, experience_journeys,
risk_of_churn_journey, ad_hoc_reactivation, reactivation_journeys, outbound_reactivation,
reactivated, reactivated_journey, vip_goodwill, goodwill, compensation, other, test.

As 10 antigas (só no front): achievements, affiliation, referral (`[EXPIRED]`); birthday,
loyalty_cs, marketing, marketing_vip, outbound_call_service, technical, welcome_offer (`[OBSERVED]`).

## Depois do CLS-3316

Uma lista por marca, a mesma do gift. A marca escreve o nome em texto livre na Administração
(até 64 caracteres, único por marca, maiúscula e minúscula iguais: `RewardOfferingReason.php:30,47-49`).
Na configuração, na oferta e no cenário, o motivo é escolhido num select, nunca digitado.

A migração acrescenta os motivos antigos à lista de cada marca. Spec: todos, com o nome igual à
chave. CLS-4744: 13 (Loyalty VIP, Sign up, 1st–4th deposit, Tournaments, RAF, Promotions,
Goodwill, Compensation, Other, Test), com nome legível. Divergência aberta, pergunta 1 e 2 ao PO.

## Falta

- Quais chaves existem de fato em `reward_configuration.reason` (pp1 por `db-query`; prod só pelo
  BigQuery `reward_configuration_reason`).
- O seed entra por SQL, que ignora o `UniqueEntity`: uma marca que já criou "Compensation" fica
  com dois. A spec aceita ("brands clean up duplicates").
