# CLS-4772: why one login leaves two `rewarded` Instant reward instances

Read-only. Worktree `/private/tmp/cls3916/celesta-promotion-4772` (no code change, no commit, stack not recreated).

## Verdict: (a), an artifact of the Behat environment

In the `test` environment the `AuthorizationJob` has **two** message handlers; in `dev` (same wiring as production) it has one.

```
bin/console debug:messenger --env=test
  JobLibrary\Job\Gateway\AuthorizationJob
      handled by App\AppBundle\MessageHandler\AuthorizationJobHandler
      handled by test.auth_message_handler
bin/console debug:messenger --env=dev
  JobLibrary\Job\Gateway\AuthorizationJob
      handled by App\AppBundle\MessageHandler\AuthorizationJobHandler
```

`config/services_test.yaml:53-57` (identical on `origin/master`, `git show origin/master:config/services_test.yaml`) defines
`test.auth_message_handler` with `class: App\AppBundle\MessageHandler\AuthorizationJobHandler`; the file's `_defaults` have
`autoconfigure: true` (`:13`), so the `#[AsMessageHandler]` attribute of the class registers it a second time.
`AuthSteps::thePlayerWithIdLogsIn()` (`tests/Acceptance/Steps/AuthSteps.php:50`) dispatches the job on the bus once; both handlers run.

Chain for each handler run: `AuthorizationJobHandler::__invoke` (`src/AppBundle/MessageHandler/AuthorizationJobHandler.php:34-36`)
-> `Standard::dispatchEngagement` -> Instant reward `EngagementHandler::postEngagement`
(`InstantReward/Handler/EngagementHandler.php:30`) -> `InstantRewardService::rewardIfEligibleOnEngagement` / `rewardNow`
(`src/AppBundle/Service/InstantRewardService.php:88-95,53-76`) -> Instant `RewardHandler::handle`. Each run creates a promotion
(engaged) and rewards it; Instant's `reengagePlayer` is a no-op (`InstantReward/Handler/RewardHandler.php:60-62`), so the
instance is not re-created by the reward itself. Two runs, two instances, `promotion` rows 1 and 2, both `rewarded`, same second
(`engaged_at` 2026-11-18 09:25:48). The existing scenario without any gift leaves the same two rows, and (with the `Background` of
my feature) the player is created by the first handler. Nothing in the Instant reward code lists the aggregator rewards twice per
instance in a way that creates a second instance: the double listing at `RewardHandler.php:70-82` (aggregator rewards, then all
rewards of the configuration) only repeats the same reward inside ONE instance, which the issuer dedupes within the call.

In production one login is one `AuthorizationJob` handled once: one instance, one reward, one gift per gift reward.

## The key `promotion:<instance id>:reward:<reward id>`

- Prevents: a second gift for the same reward of the same instance, whether by a rewarding run repeated on that instance (a
  redelivered event, a retry after a wallet failure on a bonus of the tier) or by the same reward listed twice in one call (Instant
  reward). The unique index `(player_id, idempotency_key)` is the backstop under the config lock.
- Does not prevent: a gift for a different instance. That is by design (re-engagement after rewarding creates a new instance; the
  next rewarded instance gets its own gift) and it is also what the doubled handler does in Behat. Bonuses behave the same way in
  that scenario (they are issued per rewarding run), so the test environment doubles both.
- If two real events ever created two instances of one configuration for one player (concurrent logins, for example), both would be
  rewarded and both would get the gift, as both would get the bonus today. That is the player promotion limit's and the engagement
  query's job (`PromotionConfigurationRepository::getPromotionConfigurationsToEngage`, `HAVING COUNT(p.id) = 0`), not the gift's.
  Not tested here.

## Recommendation

Leave the issuer, the key and the call sites as they are; no plan change. The key at instance granularity is the right one: a
key at the configuration level would break the "new instance, new gift" rule of the plan and the Decisions.

Only the Behat scenario carries the artifact: `features/gift/promotion/promotion_rewards_gift.feature`, the Instant reward scenario
asserts 2 gifts and 2 activities, with a comment. If Lucas prefers a scenario that does not encode the doubled handler, it can
assert "one gift per rewarded instance" instead of a literal 2 (a test-only change, amend of the implementation commit, only on
his word). Worth a separate note to whoever owns the test environment: `test.auth_message_handler` double registration.

## Item 5: `rewarding_players_based_on_reward_aggregator_tier.feature` run alone

Not checked on `origin/master`: it needs the promotion stack mounted on a master checkout, and the stack is mounted on this
worktree. What I know: on this branch the file alone fails 4 of 8 (the Memberzone mock is missing for the first job-handler call
because no player 1 exists in the DB yet) while the whole `features/deposit_tier/reward` directory passes 14 of 14. What I would run
to settle it: with the stack mounted on a clean `origin/master` checkout (after `install.sh --yes`),
`docker compose -f docker-compose.dev.yml exec -e XDEBUG_MODE=off php bin/behat features/deposit_tier/reward/rewarding_players_based_on_reward_aggregator_tier.feature`.
