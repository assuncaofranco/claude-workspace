Francisco, the spec has a Reason on the scenario bonus action, copied onto each bonus the scenario creates, but no subtask covers `celesta-scenario`.

The front is covered: CLS-4746 adds the Reason select to the scenario action and sends `reasonId` in the action options. The backend isn't. The scenario offers bonuses through the promotion offer endpoint and never sends a reason (`OfferRewardBonusActionJobHandler.php:86`), and the bonus action options reject unknown fields (`OfferBonusOptionsType.php:225`, `allow_extra_fields: false`). So once CLS-4746 ships, saving a scenario bonus action with a reason would fail with a 400.

The gift action already does this since CLS-4781 (`OfferRewardGiftActionJobHandler.php:153-155`), so the work is copying that pattern: accept an optional `reasonId` on the bonus action, validate it and send it on the offer.

Since the spec is already written, can you confirm this belongs in this story? If yes, I'd add a `celesta-scenario` subtask, blocked by CLS-4743 and blocking CLS-4746.
