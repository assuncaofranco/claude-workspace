# Staging: promotion permissions that no policy grants

Environment: `staging-1` (`backend-api.staging-1.octopostaging.com`), backoffice DB.
Checked on 2026-09-24, read only.

## Summary

Six permissions exist as rows in `permission` but have no row in `policy_permission`, so no policy
grants them and no role can inherit them. The endpoints behind them return 403 for every user in
staging, including `owner`. This is a data gap in staging, not a code bug: preprod-1 has all six
linked to `ROLE_PROMOTIONS`.

The reported case (deleting a reward from a reward aggregator, promotion #106) is one of the six.

## Evidence

Permissions are resolved at authentication time by walking
`user -> role -> role_policy -> policy -> policy_permission -> permission`, and the role string is
`ROLE_OAUTH2_` plus the uppercased `permission.name`
(`src/OAuth2Bundle/Security/Authentication/OAuth2Authenticator.php:129`). A permission with no
`policy_permission` row is unreachable from any role.

All `PS_PROMOTION_CONFIGURATION%` permissions in staging, with the policy that grants them:

| permission_id | permission_name | policy_name |
|---|---|---|
| 221 | PS_PROMOTION_CONFIGURATION_CREATE | ROLE_PROMOTIONS |
| 222 | PS_PROMOTION_CONFIGURATION_EDIT | ROLE_PROMOTIONS |
| 223 | PS_PROMOTION_CONFIGURATION_GET | ROLE_PROMOTIONS |
| 224 | PS_PROMOTION_CONFIGURATION_REPLACE_TAGS | ROLE_PROMOTIONS |
| 225 | PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATOR_DELETE | ROLE_PROMOTIONS |
| 226 | PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATOR_EDIT | ROLE_PROMOTIONS |
| 227 | PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATOR_REWARD_CREATE | ROLE_PROMOTIONS |
| **228** | **PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATOR_REWARD_DELETE** | **(none)** |
| 229 | PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATORS_CREATE | ROLE_PROMOTIONS |
| 230 | PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATORS_LIST | ROLE_PROMOTIONS |
| 231 | PS_PROMOTION_CONFIGURATION_REWARD_CREATE | ROLE_PROMOTIONS |
| **232** | **PS_PROMOTION_CONFIGURATION_REWARD_DELETE** | **(none)** |
| **233** | **PS_PROMOTION_CONFIGURATION_REWARD_EDIT** | **(none)** |
| 728 | PS_PROMOTION_CONFIGURATION_REWARD_LIST | ROLE_PROMOTIONS |
| **234** | **PS_PROMOTION_CONFIGURATION_SCHEDULE_CREATE** | **(none)** |
| **235** | **PS_PROMOTION_CONFIGURATION_SCHEDULE_DELETE** | **(none)** |
| **236** | **PS_PROMOTION_CONFIGURATION_SCHEDULE_EDIT** | **(none)** |
| 237 | PS_PROMOTION_CONFIGURATION_SCHEDULES_LIST | ROLE_PROMOTIONS |
| 238 | PS_PROMOTION_CONFIGURATION_TAGS_UPDATE | (none) |
| 239 | PS_PROMOTION_CONFIGURATION_THUMBNAIL_UPDATE | ROLE_PROMOTIONS |
| 240 | PS_PROMOTION_CONFIGURATIONS_COUNT | ROLE_PROMOTIONS |
| 241 | PS_PROMOTION_CONFIGURATIONS_LIST | ROLE_PROMOTIONS |

Permission 238 (`..._TAGS_UPDATE`) is also unlinked, but no controller asks for that name, so it is
dead data rather than a broken endpoint. The controllers use `PS_PROMOTION_CONFIGURATION_REPLACE_TAGS`.

`ROLE_PROMOTIONS` is policy id 36 in staging. It is held by 46 roles covering 239 users, so the
missing link is the only thing standing between those users and these endpoints.

## Endpoints currently returning 403 for everyone

All under `/api/gateway/domain/{domainId}`:

| Method | Path | Permission |
|---|---|---|
| DELETE | `/promotion-configuration/{id}/reward-aggregator/{aggregatorId}/reward/{rewardId}` | PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATOR_REWARD_DELETE |
| DELETE | `/promotion-configuration/{id}/reward/{rewardId}` | PS_PROMOTION_CONFIGURATION_REWARD_DELETE |
| PATCH | `/promotion-configuration/{id}/reward/{rewardId}` | PS_PROMOTION_CONFIGURATION_REWARD_EDIT |
| POST | `/promotion-configuration/{id}/schedule` | PS_PROMOTION_CONFIGURATION_SCHEDULE_CREATE |
| PUT | `/promotion-configuration/{id}/schedule/{scheduleId}` | PS_PROMOTION_CONFIGURATION_SCHEDULE_EDIT |
| DELETE | `/promotion-configuration/{id}/schedule/{scheduleId}` | PS_PROMOTION_CONFIGURATION_SCHEDULE_DELETE |

Listing and creating still work, which is why this only shows up when someone edits or deletes.

## Fix

One `policy_permission` row per permission, matched by name rather than by id, since ids differ
between environments:

```sql
INSERT IGNORE INTO policy_permission (policy_id, permission_id, created_at)
SELECT p.id, perm.id, NOW()
FROM policy p
JOIN permission perm ON perm.name = '<PERMISSION_NAME>'
WHERE p.name = 'ROLE_PROMOTIONS'
LIMIT 1;
```

Run once for each of:

```
PS_PROMOTION_CONFIGURATION_REWARD_AGGREGATOR_REWARD_DELETE
PS_PROMOTION_CONFIGURATION_REWARD_DELETE
PS_PROMOTION_CONFIGURATION_REWARD_EDIT
PS_PROMOTION_CONFIGURATION_SCHEDULE_CREATE
PS_PROMOTION_CONFIGURATION_SCHEDULE_DELETE
PS_PROMOTION_CONFIGURATION_SCHEDULE_EDIT
```

No new permission rows are needed. All six already exist.

## Why this will happen again

No migration in `celesta-backoffice/src/Migrations/` creates or links any promotion permission. They
exist in the dev fixtures (`celesta-fixtures/src/backoffice/09_permissions.yml` and
`10_policy_permissions.yml`), which is why dev works, and they were linked by hand in preprod, which
is why preprod works. Nothing owns them in staging or in production.

A migration following the existing pattern in `Version20260922000000.php` (which uses `INSERT IGNORE`
across `permission`, `policy_permission` and `role_policy`) would fix every environment at once and
survive the next database refresh. Fixing staging by hand leaves production unverified.

**Production was not checked.** If production has the same gap, this is a defect rather than a staging
data issue, and it needs a ticket.

## Not part of this gap

`PS_GIFT_LIST` and `PS_GIFT_OFFER` are demanded by the code but do not exist in staging at all. They
come from `Version20260922000000.php` (CLS-2594-CLS-3107, 2026-09-22), which has not been deployed to
staging yet. Expected, and it resolves itself on the next deploy.

## How to reproduce the check

```bash
kubectl -n celesta exec <backoffice-pod> -c backoffice-phpfpm -- \
  php bin/console dbal:run-sql "SELECT perm.id, perm.name, IFNULL(p.name, '(none)') AS policy_name FROM permission perm LEFT JOIN policy_permission pp ON pp.permission_id = perm.id LEFT JOIN policy p ON p.id = pp.policy_id WHERE perm.name LIKE 'PS_PROMOTION_CONFIGURATION%' ORDER BY perm.name"
```

Cluster `celesta-staging-1-cluster`, account 276726208200, eu-west-1, namespace `celesta`. The query
uses the application's own connection, so no database credential is involved.
