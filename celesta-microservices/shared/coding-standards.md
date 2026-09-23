# Coding Standards

Single source of truth for Celesta PHP code quality — `CLAUDE.md` and the `ticket-code`/`ticket-review` skills reference this file instead of duplicating it. Canonical source is our own `celesta-dev` library (`git@github.com:celesta-tech/celesta-dev.git`, `config/phpinsights.php` + `src/OverWrites/ForbiddenFunctionsSniffCelesta.php`), published as the private composer package `lancasters/celesta-dev` and installed into each service's `vendor/`. If this doc ever disagrees with that repo (or a service's installed copy), the repo wins — update this doc, don't trust it blindly. Not every service installs the package — verified 2026-08-31 celesta-scripts does not (no phpinsights/lint CI there at all); cite the celesta-dev repo directly in that case, not a vendor path.

## PHP Code Quality (phpinsights, Symfony preset)
- min-quality: 80 | min-architecture: 80 | min-style: 85 | min-complexity: 0 | disable-security-check: false (phpinsights' security insights run)
- Max function length: 100 lines
- Max line length: 120 characters (comments excluded)
- Excluded from analysis: `var/`, `vendor/`, `translations/`, `config/`, `public/`, `ops/`, `docker/`, `assets/`, `bin/`, `src/Migrations/`, `.github/`, `tests/`
- **Lint only checks the diff**: `make lint` runs phpinsights only on files in `git diff origin/master...<branch>` (excludes `tests/`). Any file you touch — even just restoring it — gets fully linted and must be 100% clean; untouched files can carry latent violations that never trip CI.

## Sniffs explicitly disabled (don't flag these in review — they're off, not missed)
From `phpinsights.php`'s `remove` list — the Symfony preset would otherwise check these:
- Complexity / CyclomaticComplexityIsHigh — no complexity limit is actually enforced
- DeclareStrictTypesSniff — `declare(strict_types=1)` is NOT required anywhere
- DisallowYodaComparisonSniff — Yoda comparisons not banned
- ForbiddenTraits / SuperfluousTraitNamingSniff — traits are fine, no naming rule
- ForbiddenNormalClasses / SuperfluousAbstractClassNamingSniff / SuperfluousExceptionNamingSniff — no class-naming rules for normal/abstract/exception classes
- PropertyTypeHintSniff — untyped properties (e.g. docblock-only `@var`) not flagged
- ForbiddenSetterSniff — setters allowed
- SyntaxCheck — (phpinsights' own, redundant with `php -l`/CI)
- The built-in generic `ForbiddenFunctionsSniff` is removed in favor of the custom `ForbiddenFunctionsSniffCelesta` below — one list, not two overlapping ones.

## Forbidden PHP Functions
The authoritative list lives in `celesta-dev/config/phpinsights.php` → `ForbiddenFunctionsSniffCelesta` → `forbiddenFunctions`. Entries commented with `//` in that file are NOT enforced — verify against it if these two lists ever seem to disagree.

**Enforced — use the alternative:**
| Forbidden | Use instead |
|-----------|-------------|
| `sizeof` | `count` |
| `delete` | `unset` |
| `strstr` | `strpos` |
| `is_null` | `=== null` |
| `is_resource` / `is_bool` | `=== false` |
| `intval` / `floatval` / `strval` / `boolval` / `settype` | direct cast `(int)`, `(float)`, etc. |
| `array_udiff` / `array_uintersect` | `array_diff_key` / `array_intersect_key` |
| `array_unshift` | `array_push` |
| `uasort` / `uksort` | build array to use non-u sort |
| `range` | use generators |

Plus, no alternative — never use: `dump`, `dd`, `die`, `console.log`, `exec`, `passthru`, `system`, `shell_exec`, `popen`, `pcntl_exec`, `eval`, `create_function`, `phpinfo`, `getenv`, `get_current_user`, `getcwd`, `proc_nice`, `proc_terminate`, `proc_close`, `pfsockopen`, `fsockopen`, `posix_kill`, `posix_setuid`, `extract`, `parse_str`, `putenv`, `mail`, `header`, `glob`, `stat`, `lstat`, `parse_ini_file`, `pathinfo`, plus image/file-info/exif/ftp/posix/proc/disk functions.

**Surprisingly ALLOWED** (commented out in the config despite looking risky): `array_map`, `array_search`, `array_shift`, `array_walk`, `array_unique`, `preg_replace`, `parse_url`, `count`, `array_filter`, `array_keys`, `in_array`, `implode`, `sprintf`, `ltrim`, `trim`, `array_key_exists`.

**`empty()` IS allowed** — celesta-dev deliberately puts `DisallowEmptySniff` in the config's `remove` list, unlike most strict PHP setups.

## phpinsights gotchas for a touched/new file (Symfony preset, min-style 85)
- `readonly class` **is not automatically a problem** — it was verified clean (95.1 style pts) on `celesta-backoffice`'s `CustomAttributeManager` on 2026-08-18. An older note claimed it always trips a false `[Side effects]` error; that is not universally true. If a `readonly class` really does trip it in a given file, downgrade to a plain `class` with `private readonly` promoted properties — but run phpinsights on that file first and confirm, never pre-emptively.
- Array param/return docblocks need generic syntax with a concrete item type — bare `array`/`mixed` and `string[]` are all rejected. Use `array<int, string>`, `array<string, int|string|array>`, etc.
- A typed class constant (`private const string X = ...`) trips a false uppercase-constant-name error → drop the type: `private const X = ...`.
- `ConstraintValidator::validate($value, Constraint $c)` can't get a native `array` hint on `$value` (parent is `mixed`, narrowing breaks LSP, native `mixed` disallowed) → document with `{@inheritDoc}`, don't suppress.
- A long SQL string over 120 chars: don't split a literal across `.` (trips "unnecessary string concat") — use a `<<<'SQL' ... SQL` nowdoc instead.

## Shared Libraries — never create inside a service
| What | Library |
|------|---------|
| Constants | `celesta-constants` |
| Messenger jobs | `celesta-job-library` |

## Lessons from review
Mistakes caught by a human reviewer or GitHub Copilot on a PR, worth not repeating. One bullet per lesson, dated, with a one-line "why"/fix — not a narrative.

- **2026-08-18 (Copilot, CLS-1746-CLS-2008)** — don't downgrade `readonly class` to plain `class` on a hunch: the "readonly trips Side effects" rule is file-specific, and blindly applying it weakened immutability for no gain. Verify with phpinsights on the actual file.
- **2026-08-18 (Copilot, CLS-1746-CLS-2008)** — when a controller `match`es an asset alias/type that a shared constants class already defines, use the constant, not a string literal. A literal that drifts falls through to `default =>`, which here would have silently applied the *wrong permission* instead of erroring.
- **2026-08-18 (Copilot, CLS-1746-CLS-2008)** — destructuring `[$a, $b] = explode(':', $userInput, 2)` is a 500 waiting to happen: this project converts the "Undefined array key 1" warning into an ErrorException. Use `$parts = explode(...); $b = $parts[1] ?? null;` for any request-supplied value.
- **2026-08-18 (Copilot, CLS-1746-CLS-2008)** — a blanket `$this->skipIf($schema->hasTable(...))` at the top of a migration silently skips *every* later statement in it (including unrelated `ALTER TABLE`s). Guard each DDL block on its own condition instead.
- **2026-08-31 (review, CLS-1843-CLS-1912)** — when you remove a `throw` from a shared service, that throw was an *implicit validator* for every other consumer of that service, not just the one the ticket is about. Removing `MemberzoneService::getPlayerById()`'s "currency not found" throw silently changed `RewardConfigurationController::offerReward()` from a clean 404 (it caught the exception) to a 400 whose message interpolates a null currency into empty text. Grep for consumers of the *method whose contract you relaxed*, not only for call sites of the field/getter you changed.
- **2026-08-31 (review, CLS-1843-CLS-1912)** — a `doctrine:schema:update --dump-sql` that proposes reverting the exact column your migration just changed is usually a **stale Doctrine metadata cache**, not a broken mapping. Clear it (`cache:clear` + `doctrine:cache:clear-metadata`) and re-check before "fixing" the entity or writing a second migration. Related: `make test` migrates only the *test* DB — migrate dev explicitly before any live/manual verification through it.
- **2026-09-01 (review, CLS-1911, celesta-game)** — when a test needs a wallet/HTTP mock with a status/body the existing trait helper doesn't support, extend that helper with an optional param (as done for `mockGetWalletBalance(int, ?string $data)`) instead of hand-building `static::$mockedData[]` inline in the test. Same commit did both — the inline one was the only hand-rolled mock in the whole suite, duplicating the URL/method the helper already owns.
- **2026-08-19 (self-correction, CLS-1746-CLS-2008)** — the constant-vs-literal lesson above (2026-08-18) doesn't transfer as-is to every `match` with a `default`. In `CustomAttributeManager::getClientForAsset()` (a service-layer lookup, reached *after* the permission gate), `default => throw new \Exception(...)` is correct. In `CustomAttributeController`'s two permission-*selection* `match`es (which compute the permission to pass into `denyAccessUnlessGranted()`), doing the same would run *before* that call and bypass it — a bare `\Exception` isn't `AccessDeniedException`, so Symfony's security listener never sees it and it surfaces as an uncaught 500 instead of the framework's normal 403. Keeping `default => self::PS_PLAYER_CUSTOM_ATTR_*` there is correct: it's unreachable today (route regex constrains `assetAlias`), and unlike a raw throw, it still routes through the real `denyAccessUnlessGranted()` check if it were ever reached. Lesson: before "fixing" a `default =>` arm to throw, check whether it runs before or after the permission gate — same-looking `match` shape, opposite correct answer.
- **2026-09-04 (review, CLS-1396, celesta-cms-v2)** — raising an upload/body-size limit in a webserver config that lives under `ops/docker/config/` proves nothing about deployed environments: check who actually mounts that file. In cms-v2 it is mounted only by `docker-compose.dev.yml` (not by `ops/docker/Dockerfile`), while the deployed pod runs its own nginx sidecar configured from `celesta-argocd` — which had no `client_max_body_size`, so nginx's 1MB default silently overrode the app's configured 5MB. Verify the limit end-to-end against the real environment (a >1MB upload returned nginx's HTML `413`, never reaching Strapi), not just locally.
- **2026-09-22 (review, CLS-1872, celesta-game)** — a form with `data_class => null` skips *every* entity-level constraint, `UniqueEntity` included; the DB unique index then surfaces as a 500 with the raw DBAL message (and the Backoffice's `handleV2Exception` relabels that 500 as a 400 and forwards the body). When you unbind a form from its entity, re-implement the entity constraints you still need, or catch `UniqueConstraintViolationException` into a field error.
- **2026-09-22 (review, CLS-1872, celesta-game)** — `ParameterBag::has()` is `array_key_exists`: a JSON `null` counts as present. To require a value, test `null === $bag->get($key)`, or put the rule in the form type with `PRE_SUBMIT` (capture raw keys) + `POST_SUBMIT` (add the field errors). Never rely on a data transformer for "was it sent": `Form::submit()` turns `false` into `null` before the transformer runs, so `false` and absent are already indistinguishable there.
- **2026-09-22 (review, CLS-1872, celesta-game)** — probing heterogeneous clients with `method_exists` for a "well-known" method name silently skips every client that named it differently (4 of 14 gateway clients here). Derive the per-type call from the consumer that actually uses it (the synchronizers) with a `match` on type, and test one type per branch of the probe, not only the branch that happens to be convenient.
- **2026-09-22 (review, CLS-1872, infra)** — celesta-game's (and promotion's) deployed nginx sidecar (`celesta-argocd/microservices/game/kustomize/base/game.yaml`, `log_format main`, still true after CEL-9270 on 2026-09-16 which scrubs only *headers*) logs `app_req_body:"$request_body"` and the first 1000 chars of the response as `resp_body` for every non-health request, to two sinks: `/dev/stdout` (collected by the prod-1 Datadog agent, `logs_container_collect_all = true` in `celesta-casino-terraform/celesta-prod/prod-1/datadog.tf`) and syslog → fluentbit → S3 `celesta-prod-1-s3-log-storage` under `/game/nginx/`. Any endpoint that carries a secret in a request or response body leaks it there, however clean the PHP logs are. Check the sidecar's `log_format` before claiming "no secret in any log line"; the backoffice sidecar does not log bodies. Also: read infra config from `origin/master`, not the local checkout — mine was 1281 commits behind and the first version of this finding named the wrong sink.
- **2026-09-22 (review, CLS-1872, stacked PRs)** — in a stacked chain (A → master, B → A, C → B), merging master into a *higher* branch without cascading from the bottom makes GitHub show master's commits as if they were that PR's own diff: `gh pr diff <B> --name-only` listed another ticket's controller, test, spec and plan. Merge master into the lowest branch first, then each branch into the one above it, and check with `gh pr diff --name-only` before asking for review. Merge-bases being correct (`merge-base(A,B) == tip A`) does not catch this — the leak is the *asymmetric master*, not the stacking.
- **2026-09-22 (review, CLS-1872, OpenAPI)** — `SymfonyComponents\OpenApi\Attribute\SuccessfulResponse` defaults to `response = 200`. On a create action that returns `Response::HTTP_CREATED`, pass `response: 201` explicitly or the generated doc contradicts the real status. Same family: `#[OA\Schema]` on a form type documents the *properties* but not which are mandatory — add `required: [...]` for every field the controller rejects when absent, otherwise the front builds payloads from a doc that says everything is optional.
