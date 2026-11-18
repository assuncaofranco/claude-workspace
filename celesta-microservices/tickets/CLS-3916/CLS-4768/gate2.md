# CLS-4768 gate 2

Worktree `/private/tmp/cls3916/celesta-job-library`, branch `CLS-4768`. Nothing pushed.

## 1. Implementation commit

`170f4c24a29e9c74a279da11face79a9909ad705` CLS-4768 Add the promotion source type to UserActivityJob (on top of plan commit `afd6306`).

```
 src/JobLibrary/Job/Activity/UserActivityJob.php       | 4 +++-
 tests/JobLibrary/Job/Activity/UserActivityJobTest.php | 6 ++++++
 2 files changed, 9 insertions(+), 1 deletion(-)
```

Attribution check (`git log origin/master..HEAD ... | grep -iE 'co-authored|🤖|generated with|claude code'`): printed nothing.

## 2. Tasks and criteria

| Plan item | file:line | Test |
|---|---|---|
| Task 1: `SOURCE_TYPE_PROMOTION = 'promotion'` after `SOURCE_TYPE_FRAUD` | `src/JobLibrary/Job/Activity/UserActivityJob.php:24` | `UserActivityJobTest::testPromotionSourceType` (assertSame) |
| Task 2: appended to `SOURCE_TYPES`, trailing comma added after `SOURCE_TYPE_FRAUD` | `src/JobLibrary/Job/Activity/UserActivityJob.php:118-119` | `testPromotionSourceType` (assertContains) |
| Task 3: `testPromotionSourceType()` after `testGiftOfferedEvent()` | `tests/JobLibrary/Job/Activity/UserActivityJobTest.php:213-217` | itself |
| Task 4: run Testing Strategy command | section 3 below | 12/12, 543/543 green |
| AC1: `SOURCE_TYPE_PROMOTION === 'promotion'` | `UserActivityJob.php:24` | `testPromotionSourceType` assertSame |
| AC2: `SOURCE_TYPES` contains it, eight existing entries unchanged | `UserActivityJob.php:110-119` (diff touches only the FRAUD line's comma and one added line) | `testPromotionSourceType` assertContains; existing entries untouched in the diff |
| AC3: serialization shape unchanged, existing `UserActivityJobTest` cases pass unmodified | no field, constant or serialized key changed (diff: one constant, one array entry) | existing normalize/denormalize/queue/getter cases in `UserActivityJobTest.php`, unmodified, green |

## 3. Test commands and real output

`composer install` (host, exit 0; tail of output):

```
  - Installing symfony/yaml (v7.4.23): Extracting archive
67/67 [============================] 100%
14 package suggestions were added by new dependencies, use `composer suggest` to see details.
Package doctrine/cache is abandoned, you should avoid using it. No replacement was suggested.
Package doctrine/common is abandoned, you should avoid using it. No replacement was suggested.
Generating autoload files
60 packages you are using are looking for funding.
Use the `composer fund` command to find out more!
```

`vendor/bin/phpunit tests/JobLibrary/Job/Activity/UserActivityJobTest.php`:

```
PHPUnit 10.5.67 by Sebastian Bergmann and contributors.

Runtime:       PHP 8.5.9
Configuration: /private/tmp/cls3916/celesta-job-library/phpunit.xml

............                                                      12 / 12 (100%)

Time: 00:00.005, Memory: 8.00 MB

OK (12 tests, 20 assertions)
EXIT=0
```

`vendor/bin/phpunit` (full suite):

```
PHPUnit 10.5.67 by Sebastian Bergmann and contributors.

Runtime:       PHP 8.5.9
Configuration: /private/tmp/cls3916/celesta-job-library/phpunit.xml

...............................................................  63 / 543 ( 11%)
............................................................... 126 / 543 ( 23%)
............................................................... 189 / 543 ( 34%)
............................................................... 252 / 543 ( 46%)
............................................................... 315 / 543 ( 58%)
............................................................... 378 / 543 ( 69%)
............................................................... 441 / 543 ( 81%)
............................................................... 504 / 543 ( 92%)
.......................................                         543 / 543 (100%)

Time: 00:00.103, Memory: 18.00 MB

OK (543 tests, 1373 assertions)
EXIT=0
```

No pre-existing failures. Coverage not measured locally (class constants add no lines; CI gate is 100% on approval).

## 4. Deviations

- **Tag drift (alias).** The plan was written at latest tag `v3.149` (alias `3.150`). Today the latest tag is `v3.151` (checked in `/Users/l.franco/Desktop/celesta-projects/celesta-job-library` and in the worktree after fetch), so the next free version is `3.152`. The library code does not change. Consumers must pin `"lancasters/job-library": "dev-CLS-4768 as 3.152"`; the plans of CLS-4772 and CLS-4775 say `3.150`, which already exists. Re-check `git tag --sort=-v:refname | head -1` before review and before release. The plan was not edited.
- Local PHP is 8.5.9; CI runs 8.4 (CLAUDE.md). Suite green on 8.5.9 only.
- Commit subject follows the coordinator's format (`CLS-4768 Add ...`), not the repo CLAUDE.md's `CLS-1234: ...`. No hook rejected it.
- Branch is 11 commits behind `origin/master`; built on the current base, not merged (per skill).
- Ponytail plugin not checked/used.
- No test round-trips a `promotion` job through serialize/deserialize (the plan asks only for the constant test; AC3 rests on the existing cases).

## 5. Proteus

None, per the plan.

## Update after the push (review)

- Pushed: `170f4c2` then `8b8f510` (second commit: the review asked `testPromotionSourceType` to assert the whole `SOURCE_TYPES` list with `assertSame` instead of `assertContains`; it is a second commit, not an amend, because it came after the push). PR #561.
- Review: 2 rounds, 1 finding (tests, should-fix), resolved; seven aspects No findings in both rounds. Label `sdd-reviewed`.
- Deviation from plan Task 3 wording: `assertSame` on the full list instead of `assertContains` (covers AC2 literally).
- Alias: latest tag still `v3.151` at the end; `3.152` free.

## After merging master

- Before: `git merge-base --is-ancestor v3.151 origin/CLS-4768` failed (exit 1), confirmed. Merged `origin/master` (`c61886a`, v3.151) into `CLS-4768`: merge commit `25c8ce84a8b860010d8891eae7b94f68c793237f`, message `CLS-4768 Merge master into CLS-4768`. After it `v3.151` is an ancestor. Pushed, no force.
- Conflict: only `tests/JobLibrary/Job/Activity/UserActivityJobTest.php`, both sides appended after `testGiftOfferedEvent` (master: `testGiftRequestedEvent`, `testGiftRequestRejectedEvent`, `testDepartmentEvents` and its provider; ours: `testPromotionSourceType`). Resolved keeping both, mechanical placement, our test first. `UserActivityJob.php` merged without conflict.
- `SOURCE_TYPES`: master did not change it, so the expected list in `testPromotionSourceType` needed no update.
- Diff of the branch against `origin/master` is now only the plan file, `UserActivityJob.php` (+1 constant, +1 list entry) and the 6-line test: the CLS-4768 diff is unchanged.
- `composer install` ok. `vendor/bin/phpunit`: `OK (549 tests, 1385 assertions)`.
- Latest tag `v3.151`; alias `3.152` still free.
