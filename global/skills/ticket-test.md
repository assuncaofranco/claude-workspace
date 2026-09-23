---
description: Build or extend the ticket's test scenario — always by simulating the real flow (API, real event, or real command), never by writing data into the DB directly.
argument-hint: <TICKET>
---

# ticket-test

Builds the scenario used to exercise a ticket and verify the result, after `ticket-understand` has established what's actually changing. Used standalone for a pure test/QA request too (understand + test, no code change).

## Golden rule — simulate reality
Never create data or trigger logic through an artificial shortcut. Reproduce whatever actually happens in production:

- **Missing entity for the scenario** (e.g. a promotion of a specific type, a player in a specific state) → create it through the real flow, via the Postman collection (`ticket-postman`), never via a direct `INSERT`.
- **Ticket is about an event listener** → publish the real event that triggers it, don't call the listener's code directly.
- **Ticket is about a console command** → run it via `docker exec <service>.php php bin/console <command>`, the same way a cron would invoke it in prod.
- **Database access is read-only** — use `db-query` to find out what's missing before building the scenario, and to verify the result after. Never write through it.

## Steps
1. Use `db-query` to check what already exists in the dev DB (fixtures seed most of it) and what's missing for this ticket's scenario.
2. Whatever's missing, create it for real: extend the ticket's Postman collection (see `ticket-postman`) to create it via the actual API, or trigger the actual event/command that would create it in production.
3. Build/extend the collection so it can, end to end: log in, create whatever entities the ticket needs, exercise the ticket's actual flow, and read back the resulting data — all through the collection, so there's no need to hand-write SQL to set up or check a run.
4. Run it (curl or the collection) to confirm the scenario behaves as expected before (for a bug) or after (for a fix) the code change.

## Next
For a feature/fix: hand off to `ticket-code`. For a pure test/QA request: this is the last step.
