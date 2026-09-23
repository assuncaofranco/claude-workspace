# CLS-2978 — Make game connections return all fields of the gateway configuration

Descrição do Jira, verbatim. Não editar — observações vão em arquivos separados nesta pasta.

## Problem

CLS-1458 exposed the connection list read-only, so an operator can see which gateways a brand is
connected to and their status, but every credential, URL and option behind them is changed by
engineering directly in Game_gateway_configuration.

## Solution

**Game:**

- Add `options` and `freeRoundsCancelable` to the domain gateway list DTO returned by
  `GET /api/domain/{domainId}/game-gateways`.

**Backoffice:**

- Map both fields in the game-providers normalizer: `options` as an embedded JSON object (format
  differs per gateway), `freeRoundsCancelable` as boolean. Keep camelCase.
- Update the OpenAPI schema and controller tests.
- `options` holds credentials: only include it when the caller has the "Update Game connections"
  permission (`PS_GAME_CONNECTIONS_EDIT`, wired in CLS-2980). Without it, omit the key.
