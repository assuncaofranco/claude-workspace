---
name: project_cls850_scope
description: CLS-850 scope includes DB column removal AND guarding BonusPromotionSyncListener against ClaimHandler bonuses
metadata: 
  node_type: memory
  type: project
  originSessionId: b700ffdc-19e8-42b9-8fa3-85e47cd13afe
---

CLS-850 must address two things beyond the PHP field removal already done:

1. **DB column rename** — rename deprecated BonusSubBalance columns with `old_` prefix (CLS-850-2 branch).

2. **BonusPromotionSyncListener guard** — when CLS-850 goes live, the ClaimHandler will be active and will create BonusSubBalance with `bonusId` set. `BonusPromotionSyncListener.onFlush()` will pick up those bonuses and send sync events back to Promotion, which already owns them. A guard must be added to both the insertions and updates loops:

    ```php
    if ($entity->getBonusId() !== null) {
        continue;
    }
    ```

**Why:** At CLS-1044 deploy time the ClaimHandler is not yet active, so the circular loop doesn't manifest. But it will once CLS-850 lands.

**How to apply:** When working on CLS-850, include this guard in `celesta-wallet/src/BonusBundle/EventListener/ORM/BonusPromotionSyncListener.php` alongside the field removal changes. Flag it if the ticket scope doesn't include it yet.
