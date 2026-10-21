---
name: cls3471-cls3486-decisions
description: "game-go game_transaction.errors parity (wallet code), branch base CLS-595, what PHP really stores"
metadata:
  node_type: memory
  type: project
  originSessionId: 6fc64c20-8586-41eb-9f6b-e41a902c6083
  modified: 2026-10-09T14:11:12.413Z
---

game-go stores `["wallet: http 400 (code=3)"]` instead of PHP's `[3, ...]` after a failed wallet call. Spec: `celesta-game-go/_specs/CLS-3471-CLS-3486.md` (2026-10-09).

- Branch `CLS-3471-CLS-3486` from `origin/CLS-595`, PR into CLS-595: CLS-595 owns the SoftGamings provider and the shared `internal/games` package, and sibling tickets (3470, 3472, 3475) target it. GambleHub (CLS-868) and GitSlotPark (CLS-867) have the same call sites; they're out of scope, to align with Bohdan (Linytskyi).
- The ticket is wrong that PHP stores "the wallet's own errors": the wallet answers `{code, error}` with no `errors` key, so PHP stores `[code, "HTTP/1.1 400 Bad Request returned for \"<url>\"."]` (curl-library CurlClient fallback). Wallet-not-found stores `[3, "Insufficient founds"]`, and a timeout stores `[]`.
- The ticket's `softgamings/debit.go:243` and `:547` are not wallet failures (DB config / balance parse), so they're N.

**State 2026-10-09:** implemented, not committed, and the full suite is green. The container has no Go, so tests run via `docker run golang:1.26` with the `gomodcache` volume. Newman and PP1 are left for **after review**, as Lucas asked. An `errors` object also copies PHP (`array_merge`/`json_encode`), checked against `php -r` in `game.php`.

**Review 2026-10-09 (independent agent, without the conversation's context):** found the wallet's string `code` (`NOT_FOUND`…), the Symfony title/detail message, the `:80` URL and SoftGamings with no log. All fixed; still not committed. Findings 4 (PHP marks the bet row FAILURE when the win fails in debitandcredit) and 5 (already processed + balance call fails) went in as N, out of scope. The lesson went into `coding-standards.md`. Next: commit, then Newman, then PP1.

**PHP × Go differential, local, 2026-10-09:** same request to both sides, then compared `game_transaction.errors` decoded.
- **Same on both sides (12 pairs):** code 3 on Quanta debit, debitandcredit (both rows) and credit, and on SG debit and credit; transport (`wallet.nginx` stopped) gives `[]` on both providers.
- **Not reached end-to-end:** wallet not found (the wallet returns code 3 when the currency is missing; the 404 needs a player with no wallet at all), string codes, `errors` objects, rollback/reverse sites. These are covered by unit tests only.
- **Script:** `scratchpad/parity.py`.
- **Inputs that tripped the setup:** the SG `i_gamedesc` must be `merchantID:pageCode` (`991:842`), and PHP Quanta needs `reason`.
- **Environment:** local PHP uses `WALLET_HOST=http://walletweb.docker/`, Go uses `http://wallet.nginx:80`. I brought game-go up with PHP's host.
- **Off-ticket diffs:** PHP Quanta errors carry `"code":"PAYMENT_REQUIRED"`, Go doesn't; and Go's 402 dropped the balance fields when the currency was USD.

**PP1 2026-10-09:** Lucas deployed branch `CLS-3471-CLS-3486` (`afaead4`), with PR #108 still open against CLS-595. The "Request cancelled during wallet call" improvement was dropped by the PO and reverted (`0aa8811`; the code is identical to `afaead4`).
- **SoftGamings verified:** tx 10765278 (domain 56, player 282575, game 41935 "5 Lucky Lions", gateway 19) = `[3, "HTTP/1.1 400 … http://wallet-active/…"]`. Before the deploy the format was `["wallet: http 400 (code=6)"]` (txs 10764704, 10764678).
- **Quanta verified:** tx 10765294, `t-CLS-3486-1791555050`, vault player 282570, game 81120 Strawberry Cocktail, gateway 52. I made the bet myself: the player launched the game through the Gateway, then I sent a debit to `/webhook/quanta/debit` with the basic auth from gateway 52's options, read from the DB. The vault player can't launch SoftGamings ("Restricted country").
- **Collection:** `~/.claude/postman/CLS-3471-CLS-3486/` (BO only: rounds → transactions), runs green.

**Decided 2026-10-09:** byte-for-byte parity with PHP in every case, URL message included, like every sibling ticket. I first recommended storing the wallet's text, and Lucas corrected me: in a migration the base is PHP, not "something more useful".
