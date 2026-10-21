# CLS-1546 — Deployment instructions

## Ordem

```
1. Merge celesta-qaa-proteus #618
2. Deploy celesta-backoffice #3226 (CLS-1546-CLS-3319)
3. Deploy celesta-game #1421 (CLS-1546-CLS-3318)
```

**Regra curta: backoffice antes do game, ou os dois juntos. Nunca o game sozinho antes.**

Sem migration, sem variável de ambiente nova, sem tag de biblioteca.

---

## Por quê

O game passa a **exigir** `_source`/`_sourceId` no PUT e no PATCH de maximum bet, e devolve 400 sem
eles (`MaximumBetController::getActivitySource()`). Chamadores desses dois endpoints, buscados em todos
os repositórios:

| Chamador | Manda a origem? |
|---|---|
| backoffice (`GameMaximumBetController`, PUT e PATCH) | só a partir do #3226 |
| scenario (`UpdateMaximumBetAmountActionJobHandler`, PUT) | **já manda hoje** (`propagateSource($scenarioId)`) |
| proteus (`serviceAPI.ts`, PUT) | só a partir do #618 |
| gateway | não chama PUT/PATCH, só o `maximum-bet-defaults`, que não mudou |

## Cada estado intermediário

| Estado | O que acontece |
|---|---|
| backoffice novo, game velho | o BO manda a origem e o game velho ignora. O BO já não despacha o activity e o game velho ainda não, então **as mudanças de max bet feitas nessa janela ficam sem log**. A tela funciona. |
| game novo, backoffice velho | o BO velho chama sem a origem e o game responde 400: **a edição de max bet no BO quebra**. |
| proteus novo, game velho | o parâmetro extra é ignorado; o teste passa. |
| game novo, proteus velho | o teste `player.pcgm-4` toma 400. |

Por isso o backoffice vai antes: o custo é um buraco curto no log, contra a funcionalidade fora do
ar.

## Rollback

Ordem inversa: **o game volta primeiro**. Se só o backoffice voltar com o game novo no ar, cai no
estado "game novo, backoffice velho" e a edição quebra.

Game voltando sozinho é seguro: volta a ignorar a origem, e o log de max bet some até o backoffice
também voltar.

## Infra

O game passa a publicar na fila `activity` (transport `activity_sqs_kubernetes`, igual ao da wallet).
Usa as credenciais e o prefixo SQS do kubernetes que o game já tem para `auth`. A policy de SQS da
infra é `Resource: "*"` (`celesta-casino-terraform/celesta-prod/prod-1/iam_policy.tf`), então não há
permissão nova.

## O que observar depois

- Editar o max bet de um player pelo BO: deve aparecer **uma** entrada "Bet Limit Updated" no
  histórico do player, com o agente como autor.
## Risco conhecido, fora deste ticket

Depois do deploy do game, a **aba Logs de um cenário com a action "Update maximum bet amount" quebra**
assim que o primeiro log dessa action aparece. O formatter do front
(`celesta-backoffice-front/.../scenarios/utils/formatScenarioLogs.js:72`) espera uma lista e recebe
um objeto, e roda direto no render da tabela (`ScenarioLogsTable.js:135`), então dá `TypeError` na
aba inteira. As outras telas não são afetadas, e o histórico do player renderiza normal.

A correção é do time de front. Decisão do Lucas (2026-10-07): o front não condiciona este deploy; o
PO vê o erro e o time de front corrige.
