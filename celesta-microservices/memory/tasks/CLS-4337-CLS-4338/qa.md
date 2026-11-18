---
name: cls-4337-cls-4338-qa
description: "QA of the expedite wallet #1946 (Bohdan): free-round win for a bonus held in another currency; local green, pp1 set up, game left for Francisco"
metadata:
  node_type: memory
  type: project
  originSessionId: 51a5570f-10ae-4ac0-951f-89eccd14afb3
  modified: 2026-10-30T14:58:51.220Z
---

Wallet PR #1946: `BonusResolver` finds the Promotion bonus by bonusId across all of the player's wallets (owner+domain) and books the `bonus_deposit` in the bonus wallet and currency. Unknown bonus or another player's bonus → 404.

State 2026-10-30:
- Local collection `~/.claude/postman/CLS-4337-CLS-4338/` (wallet DEV-ONLY): 18/18 on the branch; master fails the cross-currency credit.
- pp1: player 282570 (domain 56, EUR) got bonus config 7682 (10 free rounds USD, game 72631 3 Genie Wishes via CGA gw 52), bonus 1166005 claimed, USD wallet created (permanent, Lucas approved). Lucas asked Francisco to play the rounds. Verify after: `./run-pp1.sh verify "2026-10-30 14:44:28" 146.3`.

pp1 result (Francisco played): `bonus_deposit` 7.12 USD success + `bonus_withdraw` 7.12 USD success (model direct moves it to real), USD wallet realBalance 7.12, EUR real unchanged 146.30. BO game-rounds and wallet/transactions lists lag (BigQuery), so wallet balance and Francisco's DB query were the evidence. pp1 DB read (2026-10-30): wallet has only `bonus_deposit` + `bonus_withdraw` 7.12 USD at 14:53:03 for 282570 since 14:40, so the `bet` 1.00 EUR in Francisco's screenshot is not this player. Game `game_transaction` 10765482 (session 146151, grant 3507): `win` 7.12 **EUR** success, no errors. So 7.12 EUR became 7.12 USD, now proven with real data.

Open for the PO: the amount is not converted. game-go already converts to the session currency, and the wallet books the same number in the bonus currency (5 EUR → 5 USD). The PR test asserts that.

**Why:** expedite; pp1 needs a human in the game because the Quanta credit needs the session token.
**How to apply:** when Francisco reports back, run the verify folder; check free-round credit `success`, no `failure`, EUR real unchanged.
