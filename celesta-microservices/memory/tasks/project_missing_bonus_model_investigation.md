---
name: project_missing_bonus_model_investigation
description: CEL-6848 — 23 sub_balance bonus rows have null bonus_model_id; need to investigate if these bonuses are still usable in production or are dead data
metadata: 
  node_type: memory
  type: project
  originSessionId: 3022eb62-eb92-4d0d-b2ec-269deac19671
---

In the CEL-6848 migration dry run, 23 `sub_balance` rows (discr=bonus) have `bonus_model_id IS NULL`. These are skipped during migration because `bonus.reward_configuration_id` is NOT NULL in the promotion schema.

**Why:** These rows have incomplete/corrupted data in the wallet. It's unknown whether these bonuses are still active/usable in production or are effectively dead data.

**How to apply:** Before go-live, investigate in celesta-wallet whether a sub_balance bonus without a bonus_model_id can be claimed or used by a player. If yes, we need a recovery strategy. If no (they're inert), the skip is acceptable.

Known sub_balance IDs affected (from preprod, may differ in prod):
1032004, 1032005, 1032006, 1032007, 1032066, 1032067, 1032068, 1032069, 1032070, 1032071, 1032072, 1032073, 1032205, 1032209, 1032210, 1032211, 1032212, 1032213, 1032214, 1032215, 1032216, 1032218, 1032219
