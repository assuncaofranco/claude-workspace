# Architecture Patterns

## Overview
Celesta is a microservices ecosystem. Each service owns its domain and database. Services communicate via messenger jobs and HTTP APIs.

## Development Environment
- All services run in Docker containers
- Configuration via `docker-compose.dev.yml` and `.env.dev`
- External `celesta` Docker network connects all services

## Shared Libraries
| Library | Purpose | Rule |
|---------|---------|------|
| `celesta-constants` | Cross-service constants | Never define constants inside a service |
| `celesta-job-library` | Messenger job classes | Never define jobs inside a service |

## Common Patterns

### PHP Services (Symfony)
- Entry point via `docker compose -f docker-compose.dev.yml exec [service] <command>`
- PHPUnit for unit tests in `tests/`
- Behat for acceptance tests in `features/` (where applicable)
- Excluded from context: `var/`, `vendor/`, `config/`, `public/`, `src/Migrations/`

### Script Service (celesta-scripts)
- Scripts implement `MigrationInterface` with a `do()` method
- Use traits for reusability: `ParametersTrait`, `ConnectionTrait`, `LogTrait`, `LockTrait`
- Direct PDO database access across all service databases
- Container: `php` via `docker-compose.dev.yml`
