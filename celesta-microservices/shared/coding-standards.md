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

As lições que **atravessam projeto** estão em
[`../../global/shared/engineering-discipline.md`](../../global/shared/engineering-discipline.md) —
contrato de serviço compartilhado, entrada do usuário, migrations, cache, configuração que não é
montada no ambiente implantado, branches empilhadas. Ler as duas.

Aqui fica só o que depende do esquema, das bibliotecas ou da infraestrutura da Celesta. Um item por
lição, datado, com o porquê.

- **2026-09-22 (review, CLS-1872, celesta-backoffice)** — `policy` e `permission` são duas tabelas
  ligadas por `policy_permission`. A tela de Access control atribui **policies** a papéis; o portão do
  controller (`isGranted('ROLE_OAUTH2_<PERM>')`) lê **permissions**; e uma policy pode carregar
  várias — `PS_GAME_CONNECTIONS_EDIT` carrega EDIT **e** SEE, `ROLE_ACCESS_INTEGRATIONS` carrega
  `PS_INTEGRATIONS_READ`. Enumerar matriz de permissão a partir da tabela `policy`, ou do array
  `policies` que o endpoint de usuário devolve, produz células que parecem alcançáveis e não são — e
  esconde que um usuário "sem permissão de game" já passa pelo portão via a policy pai. Enumerar a
  partir de `policy_permission`, e ler com `dbal:run-sql` em preprod antes de classificar A/N/E.

- **2026-09-22 (review, CLS-1872, infra)** — o sidecar nginx implantado de `celesta-game` e de
  `celesta-promotion` registra corpo de requisição e resposta de toda requisição que não seja de
  healthcheck, para dois destinos independentes. Qualquer endpoint que carregue segredo no corpo vaza
  ali, por mais limpo que esteja o log do PHP. O sidecar do backoffice **não** registra corpos.
  Detalhe completo — arquivo, linhas, destinos e o que isso expõe hoje — em
  `~/.claude-secrets/celesta-prod-findings.md`, fora do repositório enquanto a falha estiver aberta.
  Ver também [`../memory/project_game_nginx_body_capture.md`](../memory/project_game_nginx_body_capture.md).

- **2026-08-18 (Copilot, CLS-1746-CLS-2008)** — quando um controller faz `match` sobre um alias de
  asset que uma classe de `celesta-constants` já define, usar a constante. Um literal que diverge cai
  no `default =>`, que aqui teria aplicado silenciosamente a permissão errada.

- **Constantes novas quebram o teste de constantes do backoffice, sempre.** Ver
  [`../constants-backlog.md`](../constants-backlog.md).
