---
name: cls2847-cls2848-matrix
description: "Matriz de teste (QA) do CLS-2847-CLS-2848 — remoção da flag move_bonus_to_promotion do backoffice (#3201) e gateway (#1486); critério = igual ao master com flag ON"
metadata:
  node_type: memory
  type: project
  originSessionId: ffd08648-7628-417c-b305-d88807443bdb
  modified: 2026-10-01T14:43:00.818Z
---

Papel: **testador**. PRs: backoffice #3201, gateway #1486. Sem spec/plano nas branches.

Premissa confirmada pelo Lucas em 2026-10-01: a flag já está **ON em pp1 e prod**. Logo a flag tem um
valor só e sai da matriz; o critério de toda célula é *mesma resposta que master + flag ON*.
Promotion e wallet continuam lendo a flag (não estão neste ticket) — ver [[2026-09-01-celesta-wallet-promotion]].

## Dimensão

| Dimensão | Valores | Fonte |
|---|---|---|
| Entry point | rotas abaixo | `#[Route]` nos controllers do diff; bulk action pelo tag `handler.bulk_action_item` |

Tipo de bônus / offering method **não** são dimensão aqui: o código do promotion path é idêntico ao do
master com flag ON (o diff só apaga o ramo wallet e argumentos de DI). Por isso cada entry point roda
com uma reward configuration só (`cash`, manual), salvo onde dito.

## Casos

| # | Entry point | Class | Critério observável |
|---|---|---|---|
| 1 | BO `GET /autocomplete?resource=bonus_configuration` | **A** (muda de verdade: ia ao wallet mesmo com flag ON) | devolve o nome de uma reward configuration do promotion do domínio pedido; não devolve bonus model só do wallet nem de outro domínio |
| 2 | BO `POST /bonus_configuration` (cash e free_rounds) | A-regr | 200, `id` igual ao que o promotion persistiu; `RewardConfigurationType` (form) |
| 3 | BO `PUT /bonus_configuration/{id}` | A-regr | 200, campo editado lido de volta no GET |
| 4 | BO `PATCH /bonus_configuration/{id}` (status) | A-regr | `status` = enabled |
| 5 | BO `GET /bonus_configuration/{id}` | A-regr | 200, mesmo `id` |
| 6 | BO `POST /bonus_configurations` + `/search` + `/count` | A-regr | lista contém o #2; count ≥ 1 |
| 7 | BO `POST /player/{p}/bonus_configuration/{id}/offer` | A-regr | 200, shape `RewardOfferResponse` |
| 8 | BO `GET /bonuses` + `/bonuses/count` | A-regr | lista contém o bônus do #7 com `bonusModel.id` = #2 |
| 9 | BO `POST /player/{p}/bonus/{b}/cancel` | A-regr | status canceled |
| 10 | BO `DELETE /bonus_configuration/{id}` | A-regr | 200; GET depois → 404 |
| 11 | BO `POST /bonus_configuration/{id}/thumbnail` | A-regr | `thumbnail` preenchido |
| 12 | BO promoção com reward `bonusModelId` (`BonusModelSubscriber`) | A-regr | id válido aceito; id inexistente → 400 "Provided bonus model id is invalid." |
| 13 | BO bulk action offer free bonus (worker) | A-regr | item processado, bônus aparece no #8 |
| 14 | GW `GET /bonuses` | A-regr | contém bônus oferecido |
| 15 | GW `POST /bonuses/claim` | A-regr | bônus claimed |
| 16 | GW `POST /bonus/{d}_{b}/cancel` | A-regr | canceled |
| 17 | GW `POST /payment` com bônus (`BonusFetcher`) | A-regr | depósito com bonusId de bônus OFFERED aceito |

## Achados até agora

- Merge do master no BO conflita em `BonusModelController` (OA `required: true`) e no teste dele —
  resolvido localmente, não pushado.
- **Pós-merge, `FlipperClient` vira código morto no BO** e o `WorkerStateIsolationTest` do master
  (data set "flipper cache") quebra com ServiceNotFound. Autor precisa apagar classe + `services.yaml` +
  data set ao mergear o master.
- Lucas, 2026-10-01: é **cleanup** — meta é zero flag nos dois MS; sujeira que o master reintroduzir
  conta como falha. **Apontar, não consertar.**
- **`FlipperClient` fica de propósito** (Lucas, 2026-10-01): é o client genérico para futuras flags,
  não sujeira. O que segue valendo é o teste do master que quebra por ele estar sem consumidor.
- Rerun com promotion em master, 2026-10-01: 46 requests, 84 assertions, 0 falhas.
- Sujeira restante: BO `BonusModelType`
  + registro/alias (só TODO); GW `FlipperClient` + config + stub; GW `Bonus\Transformer\BonusTransformer`
  e `Bonus\Model\Response\{Bonus,BonusList,FreeRounds,Wager}` (só TODO, só o próprio teste usa).
- Coleção: `~/.claude/postman/CLS-2847-CLS-2848/` (`run.sh` lê o vault). 17 casos verdes em 2026-10-01,
  **mas os runs depois de 13:54 UTC pegaram promotion em `CLS-412-CLS-3230`** (outra sessão trocou a
  branch) — repetir com promotion em master.
- Gotchas locais pagos: player 1 tem RG limit de depósito 1€/dia nas fixtures; `crm.li_base_domain`
  id 1 estava com `company_id=5` (owner do BO é company 1) e só funcionava por cache velho no redis —
  **nunca dar FLUSHALL no redis compartilhado**.
