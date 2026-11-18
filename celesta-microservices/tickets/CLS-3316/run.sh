#!/usr/bin/env bash
# Runs the CLS-3316 collection once, end to end (captured ids do not survive between Newman invocations), then, on
# ENV=dev only, step 9: the CLS-4744 seed and backfill command (dry run, real run, a second real run) and a read-only
# check of the database. ENV=pp1 runs the collection only: the command writes, and it is local-only.
# Credentials come from the vault at run time and are never written to a file.
# Needs Newman >= 6 (pm.execution.skipRequest), jq, and the promotion container up from the CLS-4743 + CLS-4744 branch.
# ENV=dev also runs the scenario runtime door (folders 10 and 11, CLS-5130): Newman creates the scenarios, then this script
# runs the console command `scenario:trigger:cron-scheduled-event` and drains the scenario queues, then Newman reads the
# bonuses back. It needs the scenario container up from the CLS-5130 branch (SCENARIO_CONTAINER, default scenario.php),
# plus segment, promotion, crm, backoffice and the shared MySQL and local SQS. Local only: on pp1 the scenario cron jobs
# and workers run on their own and a `* * * * *` scenario would fire every minute.
# Not run until the story's coordination releases the stacks.
set -uo pipefail
cd "$(dirname "$0")"
ENV=${ENV:-dev}
PROMOTION_CONTAINER=${PROMOTION_CONTAINER:-promotion.php}
SCENARIO_CONTAINER=${SCENARIO_CONTAINER:-scenario.php}
BO_CONTAINER=${BO_CONTAINER:-backoffice.php}

if [ "$ENV" = dev ]; then
  V=~/.claude-secrets/celesta-dev.md
  val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
  CID=$(val client_id); CSEC=$(val client_secret)
  PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
  DOMAIN=${DOMAIN:-1}; PLAYER=${PLAYER:-1}
  VARS=(--env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC"
        --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW"
        --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC"
        --env-var "username=casino+casino@gmail.com" --env-var "password=$PW")
else
  V=~/.claude-secrets/celesta-preprod.md
  val(){ grep -m1 "| \`$1\` |" "$V" | awk -F'|' '{gsub(/^[ `]+|[ `]+$/,"",$3); print $3}'; }
  DOMAIN=${DOMAIN:-56}; PLAYER=${PLAYER:-282570}
  VARS=(--env-var "BO_baseUrl=$(val BO_baseUrl)" --env-var "baseUrl=$(val baseUrl)"
        --env-var "BO_oauth_client_id=$(val BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(val BO_oauth_client_secret)"
        --env-var "BO_username=$(val BO_username)" --env-var "BO_password=$(val BO_password)"
        --env-var "oauth_client_id=$(val oauth_client_id)" --env-var "oauth_client_secret=$(val oauth_client_secret)"
        --env-var "username=$(val username)" --env-var "password=$(val password)")
fi

# free rounds cell: set the three ids of ONE free-round game of the domain, or leave them empty to skip it
FR=(--env-var "frGameId=${FR_GAME_ID:-}" --env-var "frGateway=${FR_GATEWAY:-}" --env-var "frStudio=${FR_STUDIO:-}")

printf 'Player_ID,Bonus_amount\n%s,1\n' "$PLAYER" > bulk-offer.csv   # the bulk cells upload this file

OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FAILED=0
# Folders 1-10 in one invocation (captured ids must not cross invocations); folder 11 runs after the trigger below.
# pp1 runs folders 1-9 only: the runtime door is local.
FOLDER_ARGS=()
while IFS= read -r name; do FOLDER_ARGS+=(--folder "$name"); done < <(
  jq -r '.item[].name' CLS-3316.postman_collection.json | grep -v '^11 ' | { if [ "$ENV" = dev ]; then cat; else grep -v '^10 '; fi; })
# Local only: nothing consumes the bulk-action queue here (on pp1 the BO worker does), so run a consumer for the length
# of the first Newman invocation. It stops on its own at the time limit.
if [ "$ENV" = dev ]; then
  docker exec -d "$BO_CONTAINER" php bin/console messenger:consume backoffice_bulk_action_sqs --time-limit=1800 >/dev/null 2>&1 || echo "WARN: could not start the bulk-action consumer"
fi
# --export-globals: the collection mirrors the captured variables to the globals (Newman does not export them otherwise)
npx -y newman@6 run CLS-3316.postman_collection.json "${FOLDER_ARGS[@]}" \
  --env-var "domainId=$DOMAIN" --env-var "playerId=$PLAYER" "${VARS[@]}" "${FR[@]}" \
  --working-dir . --timeout-request 60000 --delay-request 200 \
  --export-globals "$OUT/globals.json" || FAILED=1
if [ "$ENV" = dev ]; then docker exec "$BO_CONTAINER" pkill -f 'messenger:consume backoffice_bulk_action_sqs' >/dev/null 2>&1 || true; fi

if [ "$ENV" != dev ]; then
  echo "step 9 (CLS-4744 command) skipped: local only"; exit $FAILED
fi

# ---------------------------------------------------------------------------------------------------------------
# Scenario runtime door (CLS-5130 + CLS-4743): the trigger is the real console command. Nothing is written to a database.
# Folder 10 left three enabled scenarios (cron every minute, audience = a static segment with the test player). The command
# dispatches their cron events; the consumer below handles the event and action queues; folder 11 reads the bonuses back.
# Every other enabled scenario of the domain whose cron is due fires too (the fixtures have `* * * * *`): run on a throwaway stack.
# ---------------------------------------------------------------------------------------------------------------
capc(){ jq -r --arg k "$1" '[.values[]? | select(.key==$k) | .value][0] // empty' "$OUT/globals.json"; }
RT_MISSING=0
for k in rB rBName rU rUName rcR1 rcR2 rcR3 scR1 scR2 scR3 segR; do
  [ -n "$(capc "$k")" ] || { echo "runtime door: '$k' was not captured (a request in folders 1-10 failed)"; RT_MISSING=1; }
done
if [ "$RT_MISSING" = 0 ]; then
  echo "== scenario runtime door: trigger"
  docker exec "$SCENARIO_CONTAINER" php bin/console scenario:trigger:cron-scheduled-event "$DOMAIN" || { echo "  FAIL  trigger command exit status"; FAILED=1; }
  echo "== scenario runtime door: drain the event and action queues"
  # Stale messages from earlier runs and the fixture scenarios sit in the same queues: drain in rounds of 45 s until both are empty
  # (at most 8 rounds), otherwise our own actions can still be queued when folder 11 reads the bonuses.
  for round in 1 2 3 4 5 6 7 8; do
    docker exec "$SCENARIO_CONTAINER" php bin/console messenger:consume scenario_event_sqs scenario_action_sqs --time-limit=45 -vv || true
    LEFT=$(docker exec "$SCENARIO_CONTAINER" php bin/console messenger:stats 2>/dev/null | awk '$1=="scenario_event_sqs"||$1=="scenario_action_sqs"{n+=$2} END{print n+0}')
    echo "== drain round $round: $LEFT message(s) left"
    [ "$LEFT" = 0 ] && break
  done
  RTVARS=()
  for k in rB rBName rU rUName rcR1 rcR2 rcR3 scR1 scR2 scR3; do RTVARS+=(--env-var "$k=$(capc "$k")"); done
  npx -y newman@6 run CLS-3316.postman_collection.json --folder "11 Scenario runtime door: bonuses and cleanup (BO, DEV-ONLY)" \
    --env-var "domainId=$DOMAIN" --env-var "playerId=$PLAYER" "${VARS[@]}" "${RTVARS[@]}" \
    --working-dir . --timeout-request 60000 --delay-request 200 || FAILED=1
else
  FAILED=1
fi

# ---------------------------------------------------------------------------------------------------------------
# Step 9: CLS-4744. The command is the real flow; the database is only read, one SELECT per check.
# ---------------------------------------------------------------------------------------------------------------
cap(){ jq -r --arg k "$1" '[.values[]? | select(.key==$k) | .value][0] // empty' "$OUT/globals.json"; }
sql1(){ # sql1 "<scalar subquery on one line>" -> its value, NULL as the word NULL
  docker exec "$PROMOTION_CONTAINER" php bin/console dbal:run-sql "SELECT CONCAT('RESULT=', COALESCE(($1), 'NULL')) AS r" 2>&1 \
    | grep -o "RESULT=[^[:space:]\"']*" | head -1 | cut -d= -f2; }
check(){ # check "<label>" "<expected>" "<actual>"
  if [ "$2" = "$3" ]; then echo "  ok    $1"; else echo "  FAIL  $1 (expected '$2', got '$3')"; FAILED=1; fi; }
reason_of_cfg(){ sql1 "SELECT reason_id FROM reward_configuration WHERE id = $1"; }
reason_of_bonus(){ sql1 "SELECT reason_id FROM bonus WHERE id = $1"; }
bonuses_of_cfg(){ # bonuses_of_cfg <config id> <expected reason id> : every bonus of the config has it
  sql1 "SELECT CONCAT(COUNT(*), '/', SUM(reason_id <=> $2)) FROM bonus WHERE reward_configuration_id = $1"; }

for k in runTag rcLegacy rcNone rcB1 rcB2 rcB3 rcP1 rcP2 rcP3 rcA rcDel rcGift rA rB rY rZ rW bM1 bM2 bM2b bM3 bLegacy bNone; do
  [ -n "$(cap "$k")" ] || { echo "step 9: '$k' was not captured by the collection (a request before folder 9 failed)"; exit 1; }
done
C(){ cap "$1"; }

CUTOFF=$(date -u '+%Y-%m-%d %H:%M:%S')   # after every bonus of the run, so the run's bonuses are all inside the cutoff
CMD=(docker exec "$PROMOTION_CONTAINER" php bin/console reward-offering-reason:migrate-legacy "$CUTOFF")
GOODWILL_SQL="SELECT COUNT(*) FROM reward_offering_reason WHERE domain_id = $DOMAIN AND BINARY name = 'goodwill'"

echo "== before"
GOODWILL_BEFORE=$(sql1 "$GOODWILL_SQL")
check "rcLegacy has no reason_id"  NULL "$(reason_of_cfg "$(C rcLegacy)")"
check "rcNone has no reason_id"    NULL "$(reason_of_cfg "$(C rcNone)")"
check "gift config has no reason_id" NULL "$(reason_of_cfg "$(C rcGift)")"
check "bLegacy has no reason_id"   NULL "$(reason_of_bonus "$(C bLegacy)")"
check "bM2 (offered without a reason) has none" NULL "$(reason_of_bonus "$(C bM2)")"

echo "== dry run"
DRY=$("${CMD[@]}" --dry-run 2>&1); echo "$DRY"
echo "$DRY" | grep -q "Dry run, domain $DOMAIN" && echo "  ok    report names domain $DOMAIN" || { echo "  FAIL  no 'Dry run, domain $DOMAIN' line"; FAILED=1; }
echo "$DRY" | grep -q "Dry run: nothing was written." && echo "  ok    says nothing was written" || { echo "  FAIL  missing 'nothing was written'"; FAILED=1; }
check "dry run wrote no reason"      "$GOODWILL_BEFORE" "$(sql1 "$GOODWILL_SQL")"
check "dry run left rcLegacy alone"  NULL "$(reason_of_cfg "$(C rcLegacy)")"
check "dry run left bLegacy alone"   NULL "$(reason_of_bonus "$(C bLegacy)")"

echo "== real run"
REAL=$("${CMD[@]}" 2>&1); RC=$?; echo "$REAL"
check "exit status 0 (every configuration and bonus linked)" 0 "$RC"
echo "$REAL" | grep -q "Bonuses updated:" && echo "  ok    reports the bonuses updated" || { echo "  FAIL  no 'Bonuses updated:' line"; FAILED=1; }

GR=$(sql1 "SELECT MIN(id) FROM reward_offering_reason WHERE domain_id = $DOMAIN AND BINARY name = 'goodwill'")
check "one reason named exactly goodwill in the domain" 1 "$(sql1 "$GOODWILL_SQL")"
echo "== configurations (reason id of goodwill = $GR)"
for c in rcLegacy rcNone rcB2 rcP2; do check "$c (legacy key, no reasonId) -> goodwill" "$GR" "$(reason_of_cfg "$(C $c)")"; done
check "gift config stays without reason"          NULL "$(reason_of_cfg "$(C rcGift)")"
check "gift config keeps its legacy key"          goodwill "$(sql1 "SELECT reason FROM reward_configuration WHERE id = $(C rcGift)")"
check "rcLegacy keeps its legacy key"             goodwill "$(sql1 "SELECT reason FROM reward_configuration WHERE id = $(C rcLegacy)")"
for p in "rcA rA" "rcDel rY" "rcB1 rA" "rcB3 rZ" "rcP1 rA" "rcP3 rW"; do set -- $p
  check "$1 keeps the reason it had ($2)" "$(C $2)" "$(reason_of_cfg "$(C $1)")"; done

echo "== bonuses"
check "bLegacy -> goodwill"                         "$GR" "$(reason_of_bonus "$(C bLegacy)")"
check "bNone -> goodwill"                           "$GR" "$(reason_of_bonus "$(C bNone)")"
check "bM2 (rcA, none) -> the configuration's reason A"  "$(C rA)" "$(reason_of_bonus "$(C bM2)")"
check "bM2b (rcA, none) -> the configuration's reason A" "$(C rA)" "$(reason_of_bonus "$(C bM2b)")"
check "bM1 keeps the reason it was offered with (B)"     "$(C rB)" "$(reason_of_bonus "$(C bM1)")"
check "bM3 keeps its deleted reason (Y)"                 "$(C rY)" "$(reason_of_bonus "$(C bM3)")"
check "rcB2 bulk bonus -> goodwill (1 of 1)"       "1/1" "$(bonuses_of_cfg "$(C rcB2)" "$GR")"
check "rcP2 promotion bonus -> goodwill (1 of 1)"  "1/1" "$(bonuses_of_cfg "$(C rcP2)" "$GR")"
check "rcB1 bulk bonus keeps A (1 of 1)"           "1/1" "$(bonuses_of_cfg "$(C rcB1)" "$(C rA)")"
check "rcB3 bulk bonus keeps Z (1 of 1)"           "1/1" "$(bonuses_of_cfg "$(C rcB3)" "$(C rZ)")"
check "rcP1 promotion bonus keeps A (1 of 1)"      "1/1" "$(bonuses_of_cfg "$(C rcP1)" "$(C rA)")"
check "rcP3 promotion bonus keeps W (1 of 1)"      "1/1" "$(bonuses_of_cfg "$(C rcP3)" "$(C rW)")"
check "no bonus of this run's configurations is left without a reason" 0 \
  "$(sql1 "SELECT COUNT(*) FROM bonus b JOIN reward_configuration rc ON rc.id = b.reward_configuration_id WHERE rc.domain_id = $DOMAIN AND rc.name LIKE '$(C runTag)%' AND b.reason_id IS NULL")"

echo "== second real run: nothing left to do"
AGAIN=$("${CMD[@]}" 2>&1); RC=$?; echo "$AGAIN"
check "exit status 0" 0 "$RC"
echo "$AGAIN" | grep -q "Bonuses updated: 0\." && echo "  ok    Bonuses updated: 0" || { echo "  FAIL  expected 'Bonuses updated: 0.'"; FAILED=1; }
check "still one goodwill reason" 1 "$(sql1 "$GOODWILL_SQL")"

exit $FAILED
