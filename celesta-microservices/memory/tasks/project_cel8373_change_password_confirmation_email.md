---
name: project-cel8373-change-password-confirmation-email
description: "ROOT CAUSE CONFIRMED — celesta-auth's Go change_password grant never dispatches the confirmation email, since the CEL-8373 PHP→Go OAuth2 migration (2026-05-14)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9a03a386-1317-4fcd-b9c2-4cab1e93d2da
  modified: 2026-09-02T09:55:12.850Z
---

## Origin ticket
Subtask "Password change confirmation email not received — player 980304 (Spinwiz, brand 53)": test account never received the "Senha Alterada com Sucesso" confirmation email after changing their password in prod. No formal ticket id assigned yet as of 2026-09-02.

## Root cause — CONFIRMED, reproduced locally
`POST /oauth/2.0/token` on **celesta-gateway** is a thin HTTP proxy (`App\Library\AuthClient::issueToken` → `celesta-gateway/src/OAuth2/Controller/TokenController.php`) forwarding to **celesta-auth** (`AUTH_HOST=http://authweb.docker`), a separate **Go** service. celesta-gateway's own PHP `PlayerGrant`/`ChangePasswordGrant` classes (`src/OAuth2/Grant/PlayerGrant.php`) are dead code for this endpoint — confirmed by adding debug logging that never fired across ~10 real requests, before finding the proxy.

The real handler is `celesta-auth/internal/grant/change_password.go` (`ChangePasswordGrant.Issue`). It correctly dispatches:
- `dispatchLoginSideEffects` (auth/notification/fraud-login SQS messages)
- `dispatchChangePasswordActivity` (the `UserActivityJob`-equivalent)

...but **never dispatches a `TransactionalEmailJob`-equivalent** for `change_password_confirmation`. This is not a scope decision — the migration's own plan (`celesta-gateway/_plans/CEL-8373.md:337`) explicitly says `change_password.go` "adds `TransactionalEmailJob` dispatch". It was never built: `celesta-auth/internal/service/sqs/messages.go` only has 4 message constructors (`NewUserActivityMessage`, `NewAuthorizationMessage`, `NewNotificationMessage`, `NewInvalidateGameSessionMessage`) — no transactional-email equivalent exists at all, not even unwired.

**Introduced:** commit `07195a4` "CEL-8373 celesta-auth", merged 2026-05-14. Live in prod ~3.5 months as of this writing. **This is systemic, not player-980304-specific** — affects every player who changes their password via the real grant_type=change_password flow.

## What this ISN'T
- Not a data problem on the player's row (email, locale, first_name all fine — checked `li_customer` in prod for player 980304, all correct; `email_verification_status=0`/`status=lead` turned out irrelevant, no such guard exists anywhere in the validation chain).
- Not a missing BO template — `website_transactional_email` id 311 (domain 53, event `change_password_confirmation`) exists in prod with en/es-CL/pt-BR translations, well-formed.
- Not a celesta-contact/SendGrid/EDP delivery issue — the job never even gets created, so it never reaches that stage. celesta-contact's own pipeline (backoffice `WebsiteTransactionalEmailJobHandler` → `ContactClient::postEmail` → contact's `POST /emails` → `EmailMessageJob` → SendGrid/EDP → `email_history`) was separately confirmed working end-to-end in local dev once a manually-crafted `TransactionalEmailJob` was fed into the `dev-backoffice` SQS queue.

## Local repro
Collection + runbook at `~/Desktop/celesta-projects/_local-postman-collections/CEL-8373-followup/` — see [[feedback_local_postman_collections_folder]]. Verified with Newman (0 failures): `client_credentials` app token → `grant_type=change_password` (using dev fixture `li_customer.temporary_password_token='TEST_TOKEN'`, player id=1 domain=1) returns 200 with a valid JWT, but `celesta-contact`'s local `email_history` never gets a new row for the event.

Gotcha discovered while building the repro: the real `/forgot-password` endpoint on gateway DOES synchronously regenerate `li_customer.temporary_password_token` (an earlier manual test suggested otherwise — that was wrong/a timing fluke). The collection therefore does NOT call `/forgot-password` in the automated chain; it relies on a manual SQL reset of the fixture token before each run (documented in the `.md`).

## Also found along the way (real but tangential)
`celesta-backoffice`'s `WebsiteTransactionalEmailRepository::getTransactionalEmails()` sets `TranslatableListener::HINT_FALLBACK, false` — if a player's locale has no translation row for a template, the query returns empty and `WebsiteTransactionalEmailJobHandler::__invoke` silently no-ops (zero log lines either way — every log call in that handler is on an error path, none on success). Not what happened to player 980304 (their pt-BR translation existed), but a real latent gap worth remembering if a *different* locale/email ticket ever comes up silent with no error trail.

## Status / next step
Root cause fully confirmed and reproduced; fix not yet written. Fix scope: add the missing `TransactionalEmailJob`-equivalent SQS message constructor to `celesta-auth/internal/service/sqs/messages.go` and call it from `ChangePasswordGrant.Issue` (`internal/grant/change_password.go`), matching the message shape `celesta-backoffice`'s `WebsiteTransactionalEmailJobHandler` (PHP/Symfony Messenger consumer) expects to deserialize from the SQS `dev-backoffice`/prod-equivalent queue. No ticket filed yet for the fix as of 2026-09-02.
