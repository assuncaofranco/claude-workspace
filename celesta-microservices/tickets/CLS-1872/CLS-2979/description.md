# CLS-2979 — Saving an edited connection checks the configuration is correct

Descrição do Jira, verbatim. Não editar — observações vão em arquivos separados nesta pasta.

## Problem

There is no endpoint to update a game gateway configuration. `options` is free-form JSON and each
gateway expects its own keys, so a wrong or incomplete edit would break game sync, launch and free
rounds without any feedback to the user.

## Solution

**Game:**

- Add `PUT /api/domain/{domainId}/game-gateways/{id}` accepting `name`, `enabled`, `options`,
  `freeRoundsCancelable`.
- Before saving, validate: `options` is a JSON object, then build the gateway client from the
  submitted options with the same factory the synchronizer uses (fails on missing keys), then ping
  the provider with one small read call (the game list call the synchronizer starts with). Providers
  without such a call only get the key check.
- Reject with 400 and the validation or provider error; save and return the full configuration
  otherwise.

**Backoffice:**

- Add `PUT api/gateway/domain/{domainId}/integration/game-providers/{id}` behind
  `PS_GAME_CONNECTIONS_EDIT`. Forward the body to Game, return its errors unchanged.

**Backoffice front (see CLS-2981):**

- Show the returned errors on the edit form.
