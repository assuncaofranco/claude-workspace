# CLS-2980 — Add permissions to Backoffice

Descrição do Jira, verbatim. Não editar — observações e matriz em `findings.md`, nesta mesma pasta.

## Problem

Permissions `PS_GAME_CONNECTIONS_SEE` and `PS_GAME_CONNECTIONS_EDIT` exist since CLS-1821 as
placeholders under the "Update Game connections" policy, but no endpoint checks them. The
game-providers list only checks `PS_INTEGRATIONS_READ`, and there is no separate view policy.

## Solution

**Backoffice:**

- Migration: add policy `PS_GAME_CONNECTIONS_SEE` ("View Game connections") under
  `ROLE_ACCESS_INTEGRATIONS` holding the SEE permission. The existing "Update Game connections"
  policy keeps SEE and EDIT. Grant the new policy to the owner role. Add the translation in
  `messages.en.yml`.
- List endpoint: readable with `PS_INTEGRATIONS_READ`, `PS_GAME_CONNECTIONS_SEE` or
  `PS_GAME_CONNECTIONS_EDIT` (same pattern as the fraud provider controller). `options` only with
  `PS_GAME_CONNECTIONS_EDIT`.
- Update endpoint (CLS-2979): `PS_GAME_CONNECTIONS_EDIT` only.
- Tests for each role combination.

**Backoffice front:**

- Add `ROLE_GAME_CONNECTIONS_SEE` to roles and policies, and the "View Game connections" label in
  access control translations.
- Game connections: `canEdit` derives from `PS_GAME_CONNECTIONS_EDIT` instead of the current
  hard-coded `false`.
