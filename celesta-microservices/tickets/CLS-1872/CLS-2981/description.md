# CLS-2981 — Game providers cards open the connection list and detail page

Descrição do Jira, verbatim. **Ticket de outra pessoa** — está aqui só porque o CLS-2980 e o CLS-2979
dependem dele ou são dependidos por ele.

## Problem

Game provider cards on the integrations page show a status badge but are not clickable: cards only
get a link when the backend publishes an options schema, which Game does not. Users cannot see or
edit a game connection.

## Solution

**Backoffice front:**

- Make game provider cards link to `/administration/integrations/{type}`, like payment and fraud cards.
- Detail page: reuse the connections panel and connection card to list the domain's connections of
  that type with name, status, type, created and updated dates, `freeRoundsCancelable` toggle, and
  `options` in a JSON editor (CodeMirror JSON is already a dependency). Read-only without
  `PS_GAME_CONNECTIONS_EDIT`; `options` hidden when the API omits it.
- Save calls the new PUT (CLS-2979) through a new update thunk on the game providers store slice,
  replacing the current no-op write. Show API validation errors on the form.
- When `freeRoundsCancelable` changed, the save confirmation must warn: "this parameter is used by
  the providers, changing it without their advice can have unexpected side effects."
- Bear in mind permissions. Users can only see the content of `options` if they have Update permissions.
