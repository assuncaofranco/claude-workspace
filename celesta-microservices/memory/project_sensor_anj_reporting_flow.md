---
name: project-sensor-anj-reporting-flow
description: "How casino/SB events get reported to the French ANJ sensor microservice across wallet/crm/backoffice/payment, plus an open preprod 400 bug being investigated"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9fa499d3-53d5-4a95-ae35-1071a1b05b1a
  modified: 2026-08-24T13:52:12.258Z
---

Investigating (as of 2026-08-24) a 400 error in preprod when reporting sportsbook (SB, "anj",
prod-2) events to `celesta-sensor` — the ANJ regulator microservice. Casino runs as prod-1; SB has
no game, only bets. User explicitly asked to understand the flow before attempting any fix — this
memory is the flow map so that investigation doesn't have to be redone (it took a ~90-tool-call
exploration to compile).

**Update 2026-08-24:** the user downloaded `celesta-sensor` (Go, repo name `celesta-sb-sensor`) into
`celesta-projects/celesta-sensor` and built+ran it locally (`sb-sensor.api` container, port 8081,
network alias `sensorweb.docker` on the shared `celesta` network — so wallet/crm/backoffice's existing
`SENSOR_HOST=http://sensorweb.docker/` just works, no env edits needed). **Root cause of the SB 400
is now confirmed live, not just hypothesized** — see "CONFIRMED ROOT CAUSE" below. The paragraph below
about the repo being unreadable is now historical (true only for the earlier part of this
investigation, before the user supplied the repo).

**Why the flow map below still matters:** the calling code in `celesta-wallet`, `celesta-crm`,
`celesta-backoffice`, `celesta-payment` is still the source for how/when each event gets built and
sent — the sensor repo only defines the payload contract on the receiving end.

## BEST CURRENT ANSWER (live-simulated through the real wallet code, 2026-08-24)

Simulated a real `WinManager`/sportsbook win through wallet's actual entry point
(`POST /api/domain/{domainId}/wallet/{ownerId}/sb/win`, DEV-ONLY guard-signed call — the same code
path `celesta-sportsbetting` would trigger in prod) for player 1 (domain 1), against the real local
sensor. Result: **500, `InitiateException`**, logged with:
```
sensor_response: []
sensor_errors: ["Required field 'countryOfBirth' is missing or empty"]
```
`sensor_response` is empty — **the sensor was never actually contacted.** The failure happens earlier,
inside `celesta-wallet`'s own `Player\Metadata` construction (`getPlayerMetaData()` →
`new Metadata($crmCustomerData)`), which throws before `initiate()` ever builds an HTTP request. Wallet's
`Metadata` requires `countryOfBirth` (kept required even though `city_of_birth`/`department_of_birth`
were relaxed to optional — see "Known gotchas" below) — and player 1's CRM record, a perfectly ordinary
working test player, has `country_of_birth` empty. Confirmed: this is **not** the birthCity/sensor-side
400 I found earlier — it's one layer upstream of that, inside wallet, and it fires for every single
sensor-sending code path (bet/win/deposit/bonus all call the same `getPlayerMetaData()`), independent
of the sensor entirely. This is now the strongest, most directly-proven candidate for what's breaking
in preprod — check whether the SB domain's real players are missing `country_of_birth` in CRM the same
way (query in "Product-level moments" section below is close; the field to check specifically is
`country_of_birth` on `li_customer`, not `city_of_birth`/`department_of_birth`).

**CONFIRMED against real preprod data (2026-08-24, same session)**: user queried `li_customer` for
domain 213 filtered on `country_of_birth IS NULL` and found a real player — `id=282557`,
`username=cls189278097380`, `country_of_birth=NULL`. This is a real SB account in the live environment
hitting the exact condition reproduced above. The username pattern (`cls` + digits) suggests an
automated/QA-created account, consistent with CRM's own `CustomerType` form requiring
`city_of_birth`/`department_of_birth` (confirmed via the registration test earlier this session) but
**not** `country_of_birth` — so an account can pass real registration validation today while still
missing exactly the one field wallet's `Metadata` needs. **This closes the loop**: the causal chain
(gateway/CRM registration doesn't require `country_of_birth` → wallet's `Metadata` does require it →
throws before the sensor is ever reached → invisible in the sensor's own `events` table) is now backed
by a live local reproduction AND a matching real preprod row, not just code reading.

**Exact isolation of the gap in CRM's own registration validation (2026-08-24)**: CRM picks between two
form classes at registration — `FormProvider::getCustomerFormType()` returns `AnjCustomerType` for
ANJ-licensed domains, `CustomerType` otherwise. For non-ANJ domains, `username`/`first_name`/
`last_name`/`gender`/`phone_number`/`birth_date`/`currency` genuinely have no NotBlank anywhere
(deliberately relaxed, ticket `CLS-1837`, `Customer.php` moved those constraints to `import`/`profile`
groups only). **For ANJ domains — i.e. domain 213 — `AnjCustomerType::buildForm()`
(`celesta-crm/src/ApiBundle/Form/Type/AnjCustomerType.php:120-164`) explicitly re-requires the full set**:
`cityOfBirth` (`NotNull`, line 121-125), `departmentOfBirth` (`NotBlank`, line 127-131), and on POST
(registration) also `firstName`, `lastName`, `username`, `phoneNumber`, `countryPhoneCodePrefix`,
`gender`, `address`, `zipCode`, `city`, `currency`, `country`, `birthDate` (lines 145-164) — the
in-code comment literally says "Re-require the full identity/contact set for ANJ registration". **
`countryOfBirth` is absent from this file entirely** — not in the field list, not in the OpenAPI schema
docs at the top (lines 17-76) which enumerate every other field including its siblings `cityOfBirth`/
`departmentOfBirth`. This is a clean, isolated, one-field omission from a list that was clearly intended
to be exhaustive — the most likely fix is adding `countryOfBirth` next to `cityOfBirth` at line 120-125
(same `NotNull()` treatment, since both apply unconditionally to POST and PATCH, unlike the POST-only
block below them).

**Operational gotcha hit while reproducing this**: editing `.env.dev` on disk and running
`docker restart <container>` does **NOT** apply the change — this env is Docker-Compose `env_file`,
loaded into the container's process environment once at container **creation**, not re-read on restart.
Needed `docker compose -f docker-compose.dev.yml up -d --force-recreate --no-deps php` (wallet's service
is named `php`, container `wallet.php`) to actually pick up `SENSOR_HOST`. Before that fix, every sensor
call was silently a no-op (`ClientInterface::isEnabled()` bound to `%env(defined:SENSOR_HOST)%`, false
when the var isn't in the container's real env) — bets/wins returned clean 200s with zero sensor
activity and no error, which looked like "nothing sends" but was actually just this stale-env issue.
Worth remembering for any other service whose `.env.dev` gets edited for testing.

## Investigation status (updated 2026-08-24, after seeing real preprod `events` data)

Preprod domains: **56 = casino simulator** (`li_base_domain`: `vertical:["casino"]`, `license:["mga"]`),
**213 = the real SB domain** (`vertical:["sb"]`, `license:["anj"]`). Confirmed via screenshot: preprod's
`wallet.application` table has the **correct** `vertical`/`license` for domain 213 (`["sb"]`/`["anj"]`,
matching CRM exactly) — so the CRM→wallet license-sync bug below, while real in the code, is **not**
what's happening for domain 213 in preprod. Don't assume it's the cause without re-checking payment's
and fraud's copies too.

The user pulled preprod's `sensor.events` table — all 59 rows that exist. Two very different patterns:

- **Domain 56 (casino sim), 55 rows, all `event=CPTEALIM` (deposit), all `status=invalid`.** Every
  single one has `"sessionId":""` (empty string) in the stored request — that's the universal,
  100%-correlated factor, not `birthCity` (which is populated in 51/55 of them). Root cause found in
  `celesta-wallet/src/AppBundle/MessageHandler/PaymentTransactionJobHandler.php:389`:
  ```php
  sessionId: $job->getAdditionalData()['sessionId'] ?? '',
  ```
  Falls back to `''`, not to `SessionProviderInterface::SYSTEM_SESSION_ID` (`'0-sys'`) like every other
  sensor-sending code path (`BetManager`, `WinManager`, `BonusBetManager`,
  `TransactionRollbackListener` all use the `'0-sys'` fallback). The sensor's `SessionID` field is
  `validate:"required,min=1,max=256"` — an empty string fails `required`. Deposits normally have no
  active game session, so `additionalData['sessionId']` is plausibly *always* absent for real deposits
  — meaning **every deposit event through this handler 400s**, unconditionally, regardless of
  domain/vertical/license. Live-confirmed against the real sensor (see below) that this exact shape of
  payload gets rejected. **This bug is proven, but it's on the CASINO domain, not the SB one the user
  originally asked about.**
- **Domain 213 (SB), only 4 rows, all `status=success`** (`CPTEALIMOPE`/bonus-claimed,
  `CPTEAJUSTOPE`/adjustment, `CPTEABOND`/topup — bonus name `"CLS-1892 cap+sensor!!"`, clearly test
  traffic from that ticket). All have `birthCity` populated correctly. **No failure evidence for SB in
  this data at all** — so the birthCity hypothesis below is NOT yet confirmed as the actual preprod SB
  bug; it's a proven latent weakness, not a proven cause.

### Why domain 213's failure (if it happened via 2PC) might not show up in `events` at all

Read `celesta-sensor/internal/api/handler/two_phase_commit.go` closely: **`Initiate` persists a
`status=invalid` row on every validation failure (`saveInvalidSensorEvent`), but `Commit` does NOT** —
line ~186-188 just does `if err = h.validator.Validate(req); err != nil { return errs.ValidationError(err) }`
with no DB write at all. If `initiate()` succeeds (common fields present) and the failure happens at
`commit()` (fields merged in at that stage), **the event row stays stuck at `status=initiated` forever,
still holding the old initiate-time body — the actual failing payload and error are never persisted
anywhere in the sensor's own DB.** This is a real, structural gap in the sensor's auditability, and the
most likely explanation for why domain 213 shows zero failures despite the user having seen a real 400.
**Next step to confirm**: query `SELECT * FROM events WHERE domain_id=213 AND status='initiated'` for a
stuck row, and — more importantly — check **celesta-wallet's own logs** for `CommitException` (not
`InitiateException`) around domain 213/the affected player, since `CommitException::getLogContext()`
is the only place that captures the sensor's actual `sensor_response`/`sensor_errors` for a commit
failure. This is the highest-value next artifact to pull from the pods.

### birthCity — proven weakness, not yet proven to be THE preprod bug

Every event DTO in `celesta-sensor` (`internal/api/dto/v1/vault_request.go`, `VaultBaseBody`, embedded
in every event type including `BetRequest`/`WinRequest`) requires **`birthCity`**
(`validate:"required,min=1,max=64"`). `RegisterPlayerRequest` additionally requires **`birthDepartment`**
(`required,min=2,max=3,department`). `celesta-wallet/src/Library/Sensor/Player/Metadata.php::getBirthCity()`
returns `?string` — nullable, not enforced — so a player missing `city_of_birth` in CRM gets
`"birthCity": null` sent silently. Live-proven against the real running sensor:
```
POST /api/v1/domain/1/initiate {"action":"BETTING_BET", ...no birthCity...} → 400 {"errors":{"birthCity":["birthCity is a required field"]}}
same + "birthCity":"Paris" → 201 {"eventId":3}
```
Local CRM data backs up that this incompleteness is common (34/34 customers missing
`department_of_birth`, 7/34 missing `city_of_birth` too) — but until an actual failed SB bet/win/commit
is found with a null `birthCity`, this stays a strong candidate, not a confirmed cause for the SB case.

### Sensor's `allowed_domains` allow-list is a silent bypass, not a gate

`internal/api/middleware/domain_filter.go` — if `domainId` isn't in `allowed_domains`, `/initiate`
returns a **fake `201 {"eventId":0}`** and other 2PC routes return `200 {}`, with **zero validation
performed**. A domain not yet onboarded never sees any 400 regardless of payload. Locally the table was
empty until domain `1` was seeded in for testing (cache loads at boot, container needs a restart after
inserting). Worth checking whether domain 213 was *recently* added to preprod's `allowed_domains` —
that would explain "the error just started happening."

## Product-level moments that report to the sensor

Grouped by what the player/operator actually does, not by code location:

- **Apostas (sportsbook only, via celesta-wallet)**: aposta feita, aposta com bônus, ganho,
  cancelamento/rollback de aposta, ajuste manual de transação. No campo de "jogo" (gameId etc.)
  aparece em nenhum desses — cassino (game rounds) não parece reportar ao sensor via wallet.
- **Dinheiro (wallet, casino + SB dependendo da licença)**: depósito, saque pago, top-up de saldo,
  bônus creditado/retirado da carteira (estes dois últimos só disparam se a licença do domínio for
  `anj`).
- **Limites de jogo responsável (wallet + backoffice)**: jogador altera seu próprio limite de
  aposta, operador altera o limite em nome do jogador (backoffice: mudança de limite de 7 dias).
- **Ciclo de vida do jogador (celesta-crm, só se `customer->hasAnjLicense()`)**: cadastro,
  aceite de termos, confirmação de conta, confirmação de endereço, atualização de dados cadastrais,
  cadastro de conta bancária para saque, autoexclusão, fechamento de conta, tentativa de login não
  autorizado, documento de identidade verificado (KYC).

## Architecture (technical, for when the conversation goes deep again)

- **2PC protocol** (wallet, crm): `POST /api/v1/domain/{domainId}/initiate` (`{action, context}`) →
  `POST .../commit/{eventId}` (payload puro) or `POST .../rollback/{eventId}` (body vazio).
  `SensorEventDispatcher` (wallet) orchestrates initiate→commit→rollback-on-failure; most
  Managers/Listeners in `SportsbookBundle` reimplement this manually instead of using it.
- **backoffice does NOT use 2PC** — single `POST api/v1/domain/{domainId}/player/operator-responsible-gaming-limit`
  call. Worth confirming this endpoint still exists on the current celesta-sensor (the OAS dump
  reviewed only lists 4 routes: health + the 3 2PC ones).
- `domainId` comes from the player's CRM record (`Metadata::getDomainId()`), not from env config.
  `SENSOR_HOST` is one URL per service/environment — casino vs SB is NOT a different host, only a
  different `domainId` in the path.
- Vertical/license resolved via `VerticalResolver::isCasino()/isSportsBetting()/getLicense()`
  (reads `Application.vertical` from DB), same class duplicated in wallet and payment.

## Known gotchas (non-obvious, worth re-reading before any fix)

- **`Player\Metadata` required-field sets differ by service**: backoffice requires `city_of_birth`
  + `department_of_birth`; wallet treats both as optional (nullable); payment only validates
  `Metadata` at all when `isSportsBetting($domainId)` is true (`PayinHelper.php`). Since **wallet**
  is what sends bet/win events and doesn't enforce these fields, a sensor 400 demanding
  `department_of_birth`/`city_of_birth` would surface with nothing upstream having caught it.
- **The sensor client never records the HTTP status code** — confirmed as an open gap in ticket
  `CLS-1501-CLS-1502` (4xx and transient failures both just retry). To see what the sensor actually
  complained about, you have to read `sensor_response`/`sensor_errors` inside the
  `InitiateException`/`CommitException` log context — there is no structured status field.
  Existing tests only mock sensor failures as HTTP 500, never 400 — a real coverage gap.
- **ANJ-license gating is inconsistent** in wallet: `BonusWithdrawListener`/`BonusDepositListener`
  check `LICENSE_ANJ` before sending; `BetManager`/`WinManager`/`BonusBetManager` do not — they fire
  whenever `SENSOR_HOST` is configured, regardless of vertical/license. celesta-crm is consistent
  (single `SensorManager::canSend() = hasAnjLicense()` gate on every public method).
- **Three unrelated things can all surface as "400"**: (1) the sensor itself rejecting the payload,
  (2) `CrmClientException` (hardcoded 400) when fetching player metadata from CRM fails, (3) wallet's
  own `SensorDataType` form validation (e.g. `sessionId` `NotBlank`) rejecting the request before any
  HTTP call to the sensor is made. Diagnosing the preprod bug requires figuring out which of these
  three it actually is before assuming it's a sensor payload problem.
- celesta-crm's `SensorException` and `SensorNormalizer` classes are dead code (no callers found).
- **`Application.license` never propagates from CRM to wallet/payment/fraud — confirmed live, new finding (2026-08-24).**
  `celesta-crm/src/BaseBundle/EventListener/ORM/DomainCreationSubscriber.php::createJob()` builds the
  `InitiateApplicationJob` and calls `$job->setVertical($entity->getVertical())` but **never**
  `$job->setLicense(...)`, even though the job/entity both carry a `license` field. `emitUpdates()`
  on that same subscriber returns `false`, so a later license change on the domain doesn't emit
  anything either. No other job, subscriber, or console command sets `Application.license` in
  wallet/payment/fraud anywhere in these repos (searched explicitly, found nothing). Verified against
  real local data: CRM's `li_base_domain` has `license` populated (`["curacao"]`) for every domain,
  wallet's `application.license` is empty `[]` for the corresponding rows. Practical consequence: the
  ANJ gate in `VerticalResolver::getLicense()` / `BonusDepositListener` / `BonusWithdrawListener` can
  never see `LICENSE_ANJ` via this sync path, regardless of what's configured on the domain in CRM —
  those sensor calls would silently never fire (no error, just nothing sent). Not yet confirmed
  whether this is exercised differently in real prod (`celesta-brand`/`celesta-auth` aren't in this
  local checkout and might own a separate sync path this repo set doesn't show) — flagged to the user
  as new, they want it investigated/reported separately from the 400 investigation.

**How to apply:** the `countryOfBirth`-missing failure in wallet's `Metadata` class (see "BEST CURRENT
ANSWER") is the strongest lead — it's proven to fire via the real code path, happens before the sensor
is ever contacted (so it would never appear in the sensor's `events` table, which fully explains domain
213 showing zero rows despite a real failure), and is a one-line-cause, not a hypothetical. To close the
loop on preprod: check `li_customer.country_of_birth` for domain 213's players, and grep wallet's pod
logs for `"Required field 'countryOfBirth'"` or generally `InitiateException`/`CommitException` around
domain 213. The `Commit`-doesn't-persist-invalid-events gap and the birthCity sensor-side requirement
are both still real and worth fixing, but are secondary to this.
