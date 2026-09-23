# Banco — referência Celesta

O que a skill genérica `db-query` deixa de fora por ser específico daqui.
Identificadores de cluster, conta e perfil estão em [`context.yaml`](context.yaml).

## Containers locais

Nomeação `<serviço>.php`: `game.php`, `promotion.php`, `wallet.php`, `gateway.php`,
`backoffice.php`, `segment.php`, `contact.php`, `crm.php`, …

```bash
docker exec wallet.php php bin/console dbal:run-sql "<SELECT ... numa linha só>"
```

Sem `--env` para leitura — cai no banco de dev.

O serviço em Go é `dev-celesta-game-go-1` e não tem `bin/console`; se precisar, ir ao MySQL direto.

## Preprod — dentro do pod

Verificado em 2026-09-21. Os preprods de casino são **namespaces de um único cluster EKS** — nome do
cluster, conta e região em `context.yaml`. O container do PHP chama-se `<serviço>-phpfpm`
(ex.: `backoffice-phpfpm`). Namespaces: `preprod-1` a `preprod-4`.

```bash
export KUBECONFIG=<scratchpad>/kubeconfig-pp
aws eks update-kubeconfig --profile celesta-preprod --region eu-west-1 \
  --name celesta-preprod-cluster --kubeconfig "$KUBECONFIG"

kubectl --kubeconfig "$KUBECONFIG" -n preprod-1 get pods | grep <serviço>
kubectl --kubeconfig "$KUBECONFIG" -n preprod-1 exec <pod> -c <serviço>-phpfpm -- \
  php bin/console dbal:run-sql "<SELECT ...>"
```

Sessão AWS via `awsmfa` no terminal do Lucas — código do Google Authenticator, não automatizável.

## Free rounds — achar um jogo utilizável

```sql
SELECT g.id, g.name, g.free_rounds_allowed, g.game_gateway_configuration_id AS gw, gc.type, g.game_studio_id AS studio FROM game g JOIN game_gateway_configuration gc ON gc.id = g.game_gateway_configuration_id WHERE g.free_rounds_allowed = 1
```

Mapeamento para o payload do BO: `id` → `freeRoundConfiguration.gameIds[].id`,
`game_gateway_configuration_id` → `freeRoundsGameGateway`, `game_studio_id` → `freeRoundsGameStudio`.

O `type` do gateway tem que estar em `GameGatewayConstants::FREE_ROUNDS_TYPES` — `playn_go`, `quanta`,
`relax`, `redgenn`, `yggdrasil`, `evolution`, `betsoft`, `wazdan`.

Seed local conhecido: jogo Quanta id 10 / gateway 6 / studio 6.

## Armadilhas do form de reward-configuration do BO

`celesta-backoffice`, `App\GatewayBundle\Form\Type\Promotion\RewardConfiguration`:

- `freeRoundConfiguration.gameIds` e `segmentIds` no topo são arrays de **objetos** `[{"id":N}]`,
  não de inteiros.
- `gameplayRestrictionGameIds` são inteiros simples, mas cada um tem que ser um id de jogo real
  naquele domínio.
- Preferir `offeringMethod=manual`: pula segmentos por completo (`segmentIds`, recorrência e
  ocorrências só valem para `automatic`) e exige `offerValidFor`.
- `roundCount` vem do `freeRoundsRoundCount` da chamada de offer, não da configuração.
- Não existe tabela `segment` no banco do promotion.
- Campos obrigatórios de base: `name`, `type`, `model`, `offeringMethod`, `currency`,
  `validDuringDays`, `claimingEvent`, mais `wageringMultiplier` e `maxWinMultiplier`.
