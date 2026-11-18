# Testing Strategy

## All PHP Services

### Unit Tests
- Location: `/tests/`
- Runner: PHPUnit
- Command (inside Docker): `php bin/phpunit`
- All tests run inside the Docker container via `docker compose -f docker-compose.dev.yml exec [service] <command>`

## Services with Acceptance/Integration Tests

### Behat (confirmed: celesta-promotion)
- Location: `/features/`
- Runner: Behat
- Command (inside Docker): `bin/behat` (the `make test` target runs it after phpunit)
- Used for behaviour-driven acceptance tests against real service behaviour
- Run the whole suite, not one file: `features/deposit_tier/reward/*.feature` fails in isolation even on
  `master` (2026-10-27, CLS-3676), so a red isolated run proves nothing
- A step pattern like `promotion(s)` matches `promotion` or `promotions`, never the literal `(s)`;
  an "undefined" step with the right words is usually this
- Deposit steps: `the player makes a deposit of` always sends transaction 123 and the configuration
  the aggregator step creates has `playerPromotionLimit` 1, so a repeated deposit there is absorbed by
  the limit, not by the engine. For an explicit transaction id and the production `DepositJob` path use
  `I process the deposit job with transaction ID …` (`features/standard/reward/deposit_status_events.feature`)
  and `the promotion … has a player promotion limit of N`

## General Principles
- Never run tests directly on the host — always inside the Docker container
- Check the service `Makefile` for shortcut commands (`make test`)
- Tests directory is excluded from phpinsights analysis
