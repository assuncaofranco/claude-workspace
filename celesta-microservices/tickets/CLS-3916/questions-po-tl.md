Francisco, 1 to 5 are for you. Marcello, 6 is yours.

1. Gifts to order: "edited, completed and canceled" needs CLS-3865, still in Split and not linked here (`GiftConstants::STATUSES` only has `claimed`). Does this story wait for it, or do those AC move there? I'd move them and link the stories.

2. Skipped gift: is an application log enough, or must the operator see the skip, say on the promotion instance or in player activity? With a log only, nobody orders the item and nobody notices. I'd add a player activity entry, or keep log only and say so in the AC.

3. Player status: every promotion type checks the wallet flag `bonus_offer_allowed` before rewarding (`Validator/Reward/BonusOfferAllowedValidator.php:27`, refer a friend per role). When false, nothing is rewarded, so no gift. "As for promotion bonuses" means blocked by this flag. Should the gift still go through? I'd keep today's behaviour and reword the AC.

4. Offering status: enabled gift configuration, offering status inactive at rewarding time, give or skip? I'd give it, promotion bonuses ignore offering status today.

5. Reason: CLS-3316 gives every reward configuration, gift ones included, a `reasonId`. Unless you object, we copy it onto the gift (none if the configuration has none) and this part waits for CLS-3316.

6. CLS-4770 and CLS-4773 add a `Source` entity, backfill every gift and drop columns a release later. Alternative: a nullable `source_promotion_id` next to `source_user_id` and `source_scenario_id` (`Gift.php:81-86`). No backfill, no drop, no CLS-4773, and the raw SQL replay (`GiftController.php:325-326`) keeps working. Segment and bulk gifts are out of scope. Is a fourth origin planned that justifies `Source`? If not, I'd go with the column.
