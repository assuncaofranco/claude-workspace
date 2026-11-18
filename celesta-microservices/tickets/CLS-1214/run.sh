#!/usr/bin/env bash
# CLS-1214, local dev only. NOT RUN YET: wait for the coordination to release the payment, wallet, statistics and
# backoffice stacks. Credentials come from 1Password at run time (op run); nothing is written to disk but the references.
#
# Locally nothing plays the cron (supercronic in the cluster) or the queue consumers, so this script does, between the
# Newman parts: wait out the 300 s payout delay, run `withdraw-request:payout-delay`, drain the queues.
# In preprod none of that is needed: the crontab and the consumers run on their own, and the whole collection runs
# in one go (the verify requests poll until the group settles; raise pollMax for the 5-minute cron).
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${CID:-}" ]; then
  REFS=$(mktemp)
  cat > "$REFS" <<'EOF'
CID=op://Employee/claude-celesta-dev/oauth/client_id
CSEC=op://Employee/claude-celesta-dev/oauth/client_secret
PW=op://Employee/claude-celesta-dev/fixtures/seeded_password
EOF
  trap 'rm -f "$REFS"' EXIT
  op run --env-file="$REFS" -- "$0" "$@"
  exit $?
fi

COL=CLS-1214.postman_collection.json
F() { jq -r ".item[$1].name" "$COL"; }       # folder by position, so the names are never retyped
E=$(mktemp -d)/env.json; echo '{"name":"run","values":[]}' > "$E"   # carries the captured ids between the parts
FAILED=0

part() {                                       # a failing part does not stop the run
  npx -y newman run "$COL" -e "$E" --export-environment "$E" \
    --env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC" \
    --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW" \
    --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC" \
    --env-var "username=casino+casino@gmail.com" --env-var "password=$PW" \
    --env-var "pollMax=6" --env-var "pollDelayMs=3000" "$@" || FAILED=1
}

drain() {                                      # one queue, until empty or the time limit
  docker exec "$1" php bin/console messenger:consume "$2" --time-limit=20 -q || true
}

trigger() {
  echo "== waiting 305 s: the command only takes requests validated at least 300 s ago"
  sleep 305
  docker exec wallet.php php bin/console withdraw-request:payout-delay
  for _ in 1 2; do                             # twice: the payout job emits jobs that the next drain delivers
    drain wallet.php wallet_payout_sqs         # PayoutJob -> PayoutProcessor -> POST payout to payment
    drain wallet.php wallet_sqs                # payment's TransactionCreate/UpdateJob -> settle the requests
    drain statistics.php statistics_transaction_movement_sqs   # same jobs -> transaction movement with the ids
  done
}

part --folder "$(F 0)" --folder "$(F 1)" --folder "$(F 2)"    # discovery, requests, validation
trigger
part --folder "$(F 3)" --folder "$(F 4)" --folder "$(F 5)"    # group settles, player history, report
part --folder "$(F 6)"                                        # request F alone, validated after the first run
trigger
part --folder "$(F 7)"                                        # F settles and reports as today

# DEV-ONLY, optional: payment rejects an invalid list (nothing is written). Needs the guard key and payment on :82.
#   op run ... -- npx -y newman run CLS-1214.dev-only.postman_collection.json -e "$E" --env-var "guardKey=$GK"
exit $FAILED
