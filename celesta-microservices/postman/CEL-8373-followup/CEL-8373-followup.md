# CEL-8373-followup — How to test (missing change-password confirmation email)

**Feature:** confirm whether `grant_type=change_password` on the gateway (proxied to celesta-auth) dispatches the `change_password_confirmation` transactional email job, all the way through to a real provider send.

## Setup
- Import `CEL-8373-followup.postman_collection.json` and run with **No environment** — dev defaults are baked into the collection.
- Bring up `celesta-gateway`, `celesta-auth`, `celesta-crm`, `celesta-backoffice`, `celesta-contact` via `docker-compose.dev.yml` (all on `master`).
- Before each run, reset the test player's one-time reset token fixture (step 2 regenerates it for real, but step 3 needs the known value — see step 3's note):
  ```bash
  # inside celesta-crm
  docker compose -f docker-compose.dev.yml exec -T php php bin/console dbal:run-sql \
    "UPDATE li_customer SET temporary_password_token = 'TEST_TOKEN', temporary_password_token_created_at = NOW() WHERE id = 1"
  ```
- Steps 1-3 are in the Postman collection; steps 4-5 are manual (Postman/Newman is HTTP-only — it can't run `docker exec` or read SQS).
- **Run in two blocks, not one straight top-to-bottom pass** — step 2 (`/forgot-password`) legitimately regenerates `li_customer.temporary_password_token` server-side, which invalidates the `TEST_TOKEN` fixture step 3 needs. This is a real interaction, not a collection bug.
  1. Run folders **"1 - Application Auth"** + **"2 - Forgot Password"** together (`newman run <file> --folder "1 - Application Auth" --folder "2 - Forgot Password (real trigger)"`, or just those two in the Postman GUI).
  2. Re-run the SQL reset above (step 2 just clobbered it).
  3. Run folder **"3 - Change Password"** alone (`newman run <file> --folder "3 - Change Password (the call that should send the confirmation email)"`).
  Both blocks verified with Newman, 0 failures each.

## Steps
1. **[Postman]** Log in as the application (`client_credentials`) → `access_token`.
2. **[Postman]** Call `/forgot-password` for the test player — the real trigger a player uses. Regenerates `li_customer.temporary_password_token` server-side to a value we have no HTTP way to read back.
3. **[Postman]** Exchange a reset token for a player token via `grant_type=change_password` — the call that should dispatch the confirmation email. Uses `{{resetToken}}` (`TEST_TOKEN`, the fixture reset in Setup), **not** whatever step 2 just generated — Postman can't query MySQL to fetch that value. To exercise the *actual* token from step 2 instead, read it manually (`SELECT temporary_password_token FROM li_customer WHERE id=1` inside celesta-crm) and paste it into the `resetToken` variable before running this request.
4. **[Manual]** Drain the queue the job would land in, the same way a worker would in prod:
   ```bash
   # inside celesta-backoffice
   docker compose -f docker-compose.dev.yml exec -T php php bin/console messenger:consume backoffice_sqs --limit=5 --time-limit=15
   ```
5. **[Manual]** Verify — query `celesta-contact`'s local `email_history` and confirm no new row appears for this event:
   ```bash
   # inside celesta-contact
   docker compose -f docker-compose.dev.yml exec -T php php bin/console dbal:run-sql \
     "SELECT id, status, to_email, subject, created_at FROM email_history ORDER BY created_at DESC LIMIT 5"
   ```

## Variables

| Variable | Example | What it is |
|---|---|---|
| `baseUrl` | `http://localhost:93` | Gateway base url |
| `client_id` / `client_secret` | fixture values | shared dev OAuth2 client (domain_id=1) |
| `playerEmail` | `casino+casino@gmail.com` | test player (id=1, domain 1) |
| `resetToken` | `TEST_TOKEN` | dev fixture value of `li_customer.temporary_password_token` (see step 3) |
| `newPassword` | `NewPassw0rd!Repro1` | anything meeting the password policy |

Captured automatically at runtime (kept in the collection, start empty): `access_token`, `player_access_token`.

## Notes
- Steps 1-3 are real HTTP calls, runnable as-is against local dev (verified with `newman run`, 0 failures).
- Steps 4-5 need `docker exec` — no Postman equivalent exists.
- Expected result (bug present): step 3 returns 200 with a valid `change_password`-scoped JWT (test script decodes it and asserts `grant_type`); step 4 finds nothing to consume (queue was already empty — nothing was ever dispatched); step 5 shows no new `email_history` row. All three confirm `celesta-auth`'s `internal/grant/change_password.go` never dispatches the `TransactionalEmailJob` the CEL-8373 plan (`celesta-gateway/_plans/CEL-8373.md:337`) called for.
- After the fix ships (adding the missing dispatch in `celesta-auth`), re-run 1-5: step 4 should have a message to consume, and step 5 should show a new row with subject matching the confirmation template.
- Password and reset token are both single-use per run — reset the SQL fixture (Setup) between runs or step 3 fails with `invalid_credentials`.
