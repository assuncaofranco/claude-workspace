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
- Command (inside Docker): `vendor/bin/behat`
- Used for behaviour-driven acceptance tests against real service behaviour

## General Principles
- Never run tests directly on the host — always inside the Docker container
- Check the service `Makefile` for shortcut commands (`make test`)
- Tests directory is excluded from phpinsights analysis
