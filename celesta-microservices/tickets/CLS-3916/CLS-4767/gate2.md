# CLS-4767 gate 2

## 1. Commit and diff

Implementation commit: `5c046477` (`CLS-4767 Add the gift promotion reward type`) on branch `CLS-4767`, on top of the plan commit `44191300`. Not pushed.

`git diff --stat 44191300 HEAD`:

```
 src/Promotion/RewardConstants.php | 2 ++
 1 file changed, 2 insertions(+)
```

Attribution check, `git log origin/master..HEAD --format='%s%n%b' | grep -iE 'co-authored|🤖|generated with|claude code'`: printed nothing.

## 2. Tasks and criteria

| Item | Where | Test |
|---|---|---|
| Task 1: `public const TYPE_GIFT = 'gift';` after `TYPE_MATCH_BET` | `src/Promotion/RewardConstants.php:12` | none, per the plan |
| Task 2: `self::TYPE_GIFT,` appended to `TYPES` after `self::TYPE_MATCH_BET` | `src/Promotion/RewardConstants.php:20` | none, per the plan |
| Task 3: `make test` passes | section 3 | the whole suite |
| AC: `RewardConstants::TYPE_GIFT` equals `'gift'` | `src/Promotion/RewardConstants.php:12` | none, per the plan |
| AC: `TYPES` is `['future_deposit', 'free_bonus', 'free_round', 'match_deposit', 'match_bet', 'gift']` | `src/Promotion/RewardConstants.php:14-21` (gift last, existing order unchanged) | none, per the plan |
| AC: no other class in the library changes | `git diff --stat` above: one file | none, per the plan |

The repository has no `CLAUDE.md`; the code's own style was followed (untyped `public const`, like its neighbours).

## 3. Test commands and output

Command: `make test` in `/private/tmp/cls3916/celesta-constants` (Docker, no PHP on the host). Exit code 0. Full output (the first run also installed `vendor/`, which is git-ignored; `git status` was clean apart from the edited file):

```
docker run --rm --user 502:20 -e HOME=/tmp -e COMPOSER_HOME=/tmp/composer -e COMPOSER_CACHE_DIR=/tmp/composer-cache  -v /Users/l.franco/.composer/auth.json:/tmp/composer/auth.json:ro -v /private/tmp/cls3916/celesta-constants:/app -w /app celesta-constants-php:8.3 composer install --no-scripts --no-interaction
Composer could not detect the root package (lancasters/constants) version, defaulting to '1.0.0'. See https://getcomposer.org/root-version
Installing dependencies from lock file (including require-dev)
Verifying lock file contents can be installed on current platform.
Package operations: 71 installs, 0 updates, 0 removals
  - Downloading squizlabs/php_codesniffer (3.7.2)
  - Downloading dealerdirect/phpcodesniffer-composer-installer (v1.0.0)
  - Downloading composer/pcre (3.1.1)
  - Downloading symfony/polyfill-mbstring (v1.28.0)
  - Downloading symfony/polyfill-ctype (v1.28.0)
  - Downloading symfony/filesystem (v6.4.0)
  - Downloading symfony/deprecation-contracts (v3.4.0)
  - Downloading symfony/var-exporter (v6.4.2)
  - Downloading psr/container (2.0.2)
  - Downloading symfony/service-contracts (v3.4.1)
  - Downloading symfony/dependency-injection (v6.4.2)
  - Downloading symfony/config (v6.4.0)
  - Downloading pdepend/pdepend (2.16.2)
  - Downloading psr/log (3.0.0)
  - Downloading composer/xdebug-handler (3.0.3)
  - Downloading phpmd/phpmd (2.13.0)
  - Downloading symfony/process (v6.4.2)
  - Downloading symfony/http-client-contracts (v3.4.0)
  - Downloading symfony/http-client (v6.4.2)
  - Downloading symfony/finder (v6.4.0)
  - Downloading symfony/polyfill-intl-normalizer (v1.28.0)
  - Downloading symfony/polyfill-intl-grapheme (v1.28.0)
  - Downloading symfony/string (v6.4.2)
  - Downloading symfony/console (v6.4.2)
  - Downloading psr/cache (3.0.0)
  - Downloading symfony/cache-contracts (v3.4.0)
  - Downloading symfony/cache (v6.4.2)
  - Downloading phpstan/phpdoc-parser (1.25.0)
  - Downloading slevomat/coding-standard (8.14.1)
  - Downloading sebastian/diff (5.1.1)
  - Downloading psr/simple-cache (2.0.0)
  - Downloading php-parallel-lint/php-parallel-lint (v1.3.2)
  - Downloading league/container (4.2.0)
  - Downloading justinrainbow/json-schema (v5.2.13)
  - Downloading symfony/stopwatch (v6.4.0)
  - Downloading symfony/polyfill-php81 (v1.28.0)
  - Downloading symfony/polyfill-php80 (v1.28.0)
  - Downloading symfony/options-resolver (v6.4.0)
  - Downloading psr/event-dispatcher (1.0.0)
  - Downloading symfony/event-dispatcher-contracts (v3.4.0)
  - Downloading symfony/event-dispatcher (v6.4.2)
  - Downloading composer/semver (3.4.0)
  - Downloading friendsofphp/php-cs-fixer (v3.46.0)
  - Downloading sebastian/cli-parser (2.0.1)
  - Downloading phpunit/php-file-iterator (4.1.0)
  - Downloading cmgmyr/phploc (8.0.3)
  - Downloading nunomaduro/phpinsights (v2.11.0)
  - Downloading lancasters/celesta-dev (v1.24)
  - Downloading sebastian/version (4.0.1)
  - Downloading sebastian/type (4.0.0)
  - Downloading sebastian/recursion-context (5.0.2)
  - Downloading sebastian/object-reflector (3.0.0)
  - Downloading sebastian/object-enumerator (5.0.0)
  - Downloading sebastian/global-state (6.0.2)
  - Downloading sebastian/exporter (5.1.4)
  - Downloading sebastian/environment (6.1.0)
  - Downloading sebastian/comparator (5.0.5)
  - Downloading sebastian/code-unit (2.0.0)
  - Downloading phpunit/php-timer (6.0.0)
  - Downloading phpunit/php-text-template (3.0.1)
  - Downloading phpunit/php-invoker (4.0.0)
  - Downloading theseer/tokenizer (1.3.1)
  - Downloading nikic/php-parser (v5.9.0)
  - Downloading sebastian/lines-of-code (2.0.2)
  - Downloading sebastian/complexity (3.2.0)
  - Downloading sebastian/code-unit-reverse-lookup (3.0.0)
  - Downloading phpunit/php-code-coverage (10.1.16)
  - Downloading phar-io/version (3.2.1)
  - Downloading phar-io/manifest (2.0.4)
  - Downloading myclabs/deep-copy (1.14.0)
  - Downloading phpunit/phpunit (10.5.66)
  0/71 [>---------------------------]   0%
 10/71 [===>------------------------]  14%
 19/71 [=======>--------------------]  26%
 24/71 [=========>------------------]  33%
 29/71 [===========>----------------]  40%
 36/71 [==============>-------------]  50%
 45/71 [=================>----------]  63%
 56/71 [======================>-----]  78%
 62/71 [========================>---]  87%
 66/71 [==========================>-]  92%
 71/71 [============================] 100%
  - Installing squizlabs/php_codesniffer (3.7.2): Extracting archive
  - Installing dealerdirect/phpcodesniffer-composer-installer (v1.0.0): Extracting archive
  - Installing composer/pcre (3.1.1): Extracting archive
  - Installing symfony/polyfill-mbstring (v1.28.0): Extracting archive
  - Installing symfony/polyfill-ctype (v1.28.0): Extracting archive
  - Installing symfony/filesystem (v6.4.0): Extracting archive
  - Installing symfony/deprecation-contracts (v3.4.0): Extracting archive
  - Installing symfony/var-exporter (v6.4.2): Extracting archive
  - Installing psr/container (2.0.2): Extracting archive
  - Installing symfony/service-contracts (v3.4.1): Extracting archive
  - Installing symfony/dependency-injection (v6.4.2): Extracting archive
  - Installing symfony/config (v6.4.0): Extracting archive
  - Installing pdepend/pdepend (2.16.2): Extracting archive
  - Installing psr/log (3.0.0): Extracting archive
  - Installing composer/xdebug-handler (3.0.3): Extracting archive
  - Installing phpmd/phpmd (2.13.0): Extracting archive
  - Installing symfony/process (v6.4.2): Extracting archive
  - Installing symfony/http-client-contracts (v3.4.0): Extracting archive
  - Installing symfony/http-client (v6.4.2): Extracting archive
  - Installing symfony/finder (v6.4.0): Extracting archive
  - Installing symfony/polyfill-intl-normalizer (v1.28.0): Extracting archive
  - Installing symfony/polyfill-intl-grapheme (v1.28.0): Extracting archive
  - Installing symfony/string (v6.4.2): Extracting archive
  - Installing symfony/console (v6.4.2): Extracting archive
  - Installing psr/cache (3.0.0): Extracting archive
  - Installing symfony/cache-contracts (v3.4.0): Extracting archive
  - Installing symfony/cache (v6.4.2): Extracting archive
  - Installing phpstan/phpdoc-parser (1.25.0): Extracting archive
  - Installing slevomat/coding-standard (8.14.1): Extracting archive
  - Installing sebastian/diff (5.1.1): Extracting archive
  - Installing psr/simple-cache (2.0.0): Extracting archive
  - Installing php-parallel-lint/php-parallel-lint (v1.3.2): Extracting archive
  - Installing league/container (4.2.0): Extracting archive
  - Installing justinrainbow/json-schema (v5.2.13): Extracting archive
  - Installing symfony/stopwatch (v6.4.0): Extracting archive
  - Installing symfony/polyfill-php81 (v1.28.0): Extracting archive
  - Installing symfony/polyfill-php80 (v1.28.0): Extracting archive
  - Installing symfony/options-resolver (v6.4.0): Extracting archive
  - Installing psr/event-dispatcher (1.0.0): Extracting archive
  - Installing symfony/event-dispatcher-contracts (v3.4.0): Extracting archive
  - Installing symfony/event-dispatcher (v6.4.2): Extracting archive
  - Installing composer/semver (3.4.0): Extracting archive
  - Installing friendsofphp/php-cs-fixer (v3.46.0): Extracting archive
  - Installing sebastian/cli-parser (2.0.1): Extracting archive
  - Installing phpunit/php-file-iterator (4.1.0): Extracting archive
  - Installing cmgmyr/phploc (8.0.3): Extracting archive
  - Installing nunomaduro/phpinsights (v2.11.0): Extracting archive
  - Installing lancasters/celesta-dev (v1.24): Extracting archive
  - Installing sebastian/version (4.0.1): Extracting archive
  - Installing sebastian/type (4.0.0): Extracting archive
  - Installing sebastian/recursion-context (5.0.2): Extracting archive
  - Installing sebastian/object-reflector (3.0.0): Extracting archive
  - Installing sebastian/object-enumerator (5.0.0): Extracting archive
  - Installing sebastian/global-state (6.0.2): Extracting archive
  - Installing sebastian/exporter (5.1.4): Extracting archive
  - Installing sebastian/environment (6.1.0): Extracting archive
  - Installing sebastian/comparator (5.0.5): Extracting archive
  - Installing sebastian/code-unit (2.0.0): Extracting archive
  - Installing phpunit/php-timer (6.0.0): Extracting archive
  - Installing phpunit/php-text-template (3.0.1): Extracting archive
  - Installing phpunit/php-invoker (4.0.0): Extracting archive
  - Installing theseer/tokenizer (1.3.1): Extracting archive
  - Installing nikic/php-parser (v5.9.0): Extracting archive
  - Installing sebastian/lines-of-code (2.0.2): Extracting archive
  - Installing sebastian/complexity (3.2.0): Extracting archive
  - Installing sebastian/code-unit-reverse-lookup (3.0.0): Extracting archive
  - Installing phpunit/php-code-coverage (10.1.16): Extracting archive
  - Installing phar-io/version (3.2.1): Extracting archive
  - Installing phar-io/manifest (2.0.4): Extracting archive
  - Installing myclabs/deep-copy (1.14.0): Extracting archive
  - Installing phpunit/phpunit (10.5.66): Extracting archive
  0/69 [>---------------------------]   0%
 14/69 [=====>----------------------]  20%
 23/69 [=========>------------------]  33%
 37/69 [===============>------------]  53%
 45/69 [==================>---------]  65%
 51/69 [====================>-------]  73%
 59/69 [=======================>----]  85%
 63/69 [=========================>--]  91%
 69/69 [============================] 100%
Generating autoload files
59 packages you are using are looking for funding.
Use the `composer fund` command to find out more!
PHP CodeSniffer Config installed_paths set to ../../slevomat/coding-standard
docker run --rm --user 502:20 -e HOME=/tmp -e COMPOSER_HOME=/tmp/composer -e COMPOSER_CACHE_DIR=/tmp/composer-cache  -v /Users/l.franco/.composer/auth.json:/tmp/composer/auth.json:ro -v /private/tmp/cls3916/celesta-constants:/app -w /app celesta-constants-php:8.3 vendor/bin/phpunit  
PHPUnit 10.5.66 by Sebastian Bergmann and contributors.

Runtime:       PHP 8.3.36
Configuration: /app/phpunit.xml

...............................................................  63 / 130 ( 48%)
............................................................... 126 / 130 ( 96%)
....                                                            130 / 130 (100%)

Time: 00:00.034, Memory: 8.00 MB

OK (130 tests, 857 assertions)
make test  0.05s user 0.05s system 1% cpu 8.481 total
```

Tag check: `git -C /Users/l.franco/Desktop/celesta-projects/celesta-constants tag --sort=-v:refname | head -1` prints `v1.368` (after `git fetch --tags origin`). The alias `1.369` is still free.

## 4. Deviations from the plan

None.

## 5. Proteus

None, per the plan.

## After merging master

`v1.369` (CLS-5181, player currency update permission) was released after this branch was cut, so the alias `1.369` is taken and consumers use `dev-CLS-4767 as 1.370`. `v1.369` was not an ancestor of `origin/CLS-4767`; `origin/master` was merged into the branch.

- Merge commit: `fd3438e7` (`CLS-4767 Merge master into CLS-4767`), plain merge, no rebase, no force. Pushed with `git push origin CLS-4767:CLS-4767`.
- Conflicts: none. The merge brought `.sdd/_plans/CLS-5181.md`, `src/Backoffice/PlayerFieldPermissions.php` and `tests/Backoffice/PlayerFieldPermissionsTest.php` from master.
- The CLS-4767 diff against `origin/master` (excluding `.sdd`) is unchanged: `src/Promotion/RewardConstants.php | 2 ++`. No new review round needed.
- Attribution grep on the merge commit: printed nothing.
- `v1.369` is now an ancestor of `origin/CLS-4767`.

`make test` output after the merge (`make test` exit 0; the docker run command line is omitted):

```
PHPUnit 10.5.66 by Sebastian Bergmann and contributors.

Runtime:       PHP 8.3.36
Configuration: /app/phpunit.xml

...............................................................  63 / 132 ( 47%)
............................................................... 126 / 132 ( 95%)
......                                                          132 / 132 (100%)

Time: 00:00.045, Memory: 8.00 MB

OK (132 tests, 860 assertions)
```
