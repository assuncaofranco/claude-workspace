---
description: Query a Celesta service's database straight from its container — read-only, for discovering real ids/columns before building a test scenario or verifying a fix's result.
allowed-tools: Bash(docker exec:*)
---

# db-query

Read-only lookup into any Celesta service's database, from the host, without a DB client:

```
docker exec <service>.php php bin/console dbal:run-sql "<SELECT ...>"
```

Container naming is `<service>.php` (`game.php`, `promotion.php`, `wallet.php`, `gateway.php`, `backoffice.php`, `segment.php`, `contact.php`, `crm.php`, ...). The Go service is `dev-celesta-game-go-1` — no `bin/console`, hit MySQL directly if needed. No `--env` needed for a read (defaults to the dev DB).

## Rules
- **Read-only. Never write through this.** If a ticket's scenario needs a row that doesn't exist, create it through the real flow (Postman/API, an event, or a console command) — see `ticket-test`. This command is only for diagnosing what's missing and verifying what a fix produced.
- **Always write the SQL on ONE line.** A multi-line string (e.g. a heredoc or a quoted query starting with a newline) makes `dbal:run-sql` return a bare `[OK] 0 rows affected.` instead of results — it looks exactly like "no rows matched", so it silently produces wrong conclusions. Verified 2026-08-18: the same `information_schema` query returned nothing multi-line and full results single-line.
- **Never guess column names.** Discover them first:
  ```sql
  SELECT GROUP_CONCAT(COLUMN_NAME) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '<table>'
  ```

## Known-useful lookups

**Foreign keys on a table** (settles "can table X exist without table Y?" — a `CREATE TABLE` with an FK cannot run before its parent exists):
```sql
SELECT COLUMN_NAME, REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='<table>' AND REFERENCED_TABLE_NAME IS NOT NULL
```


**Free-round reward-configuration — find a usable game:**
```sql
SELECT g.id, g.name, g.free_rounds_allowed, g.game_gateway_configuration_id AS gw, gc.type, g.game_studio_id AS studio FROM game g JOIN game_gateway_configuration gc ON gc.id = g.game_gateway_configuration_id WHERE g.free_rounds_allowed = 1
```
Map the row to the BO payload: `id` → `freeRoundConfiguration.gameIds[].id`, `game_gateway_configuration_id` → `freeRoundsGameGateway`, `game_studio_id` → `freeRoundsGameStudio`. The gateway `type` must be in `GameGatewayConstants::FREE_ROUNDS_TYPES` (playn_go, quanta, relax, redgenn, yggdrasil, evolution, betsoft, wazdan). Known-good local seed: Quanta game id 10 / gateway 6 / studio 6.

**BO reward-configuration form gotchas** (`celesta-backoffice` `GatewayBundle`, `App\GatewayBundle\Form\Type\Promotion\RewardConfiguration`): `freeRoundConfiguration.gameIds` and top-level `segmentIds` are arrays of OBJECTS `[{"id":N}]`, not plain ints. `gameplayRestrictionGameIds` are plain ints but each must be a real game id in the domain. Prefer `offeringMethod=manual` — skips segments entirely (segmentIds/recurrence/occurrences only apply to `automatic`); needs `offerValidFor`; `roundCount` comes from the offer call's `freeRoundsRoundCount`, not the config. There is no `segment` table in the promotion DB. Base required fields: name, type, model, offeringMethod, currency, validDuringDays, claimingEvent, plus `wageringMultiplier` + `maxWinMultiplier`.

## Preprod — mesma ideia, dentro do pod

Verificado em 2026-09-21 no `preprod-1`. Os preprods de casino são **namespaces de um único cluster
EKS**, `celesta-preprod-cluster` (conta 852102753749, eu-west-1), então dá para rodar o mesmo
`dbal:run-sql` dentro do container do serviço. **Não é preciso credencial de banco nenhuma** — a
conexão é a da própria aplicação. Nada de senha de RDS para guardar, nada que possa vazar num repo.

**Produção nunca.** Só preprod, e só leitura.

```bash
export KUBECONFIG=<scratchpad>/kubeconfig-pp                      # nunca o kubeconfig padrão do Lucas
aws eks update-kubeconfig --profile celesta-preprod --region eu-west-1 \
  --name celesta-preprod-cluster --kubeconfig "$KUBECONFIG"

kubectl --kubeconfig "$KUBECONFIG" -n preprod-1 get pods | grep <serviço>
kubectl --kubeconfig "$KUBECONFIG" -n preprod-1 exec <pod> -c <serviço>-phpfpm -- \
  php bin/console dbal:run-sql "<SELECT ... numa linha só>"
```

- **Precisa de sessão AWS viva**: `awsmfa` no terminal do Lucas — código do Google Authenticator, não
  dá para rodar sozinho. Erro `ExpiredToken` em qualquer comando = pedir para ele rodar e tentar de novo.
- **O pod tem mais de um container**: o nome do container do PHP é `<serviço>-phpfpm`
  (ex.: `backoffice-phpfpm`); sem `-c` o kubectl cai no primeiro e pode ser o nginx.
- **Namespace sempre explícito** (`preprod-1`..`preprod-4`) em todo comando, para não errar de ambiente
  por descuido. O namespace é o ambiente.
- A regra de SQL numa linha só vale igual aqui.

**Por que isso importa:** preprod é alterado à mão por muita gente, inclusive nas tabelas de permissão.
Boa parte do que parece bug de código é dado inconsistente, e pela API isso é invisível.
