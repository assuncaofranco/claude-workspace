#!/usr/bin/env bash
# Local dev only. Credentials come from the vault at run time.
# Nothing consumes the promotion queue locally, so the deposit jobs are pushed to localsqs by hand and
# promotion's consumer is run between the Newman parts, with --limit so every copy is drained.
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-dev.md
val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
CID=$(val client_id); CSEC=$(val client_secret)
PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
GK=$(grep -m1 'GUARD_KEY=' "$V" | sed -E 's/.*GUARD_KEY=([a-z]+).*/\1/')
Q=http://localhost:9324/000000000000/dev-promotion
export AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x AWS_DEFAULT_REGION=eu-west-1
TX=$(date +%s)   # transaction ids must be new per run: tx1..tx5 = TX+1..TX+5

push(){ # push <transactionId> <status> [copies]
  local body; body=$(printf '{"playerId":%s,"domainId":%s,"transactionId":%s,"status":"%s","amount":50.0,"currency":"EUR","rewardIds":null}' 1 1 "$1" "$2")
  for _ in $(seq 1 "${3:-1}"); do
    aws --endpoint-url http://localhost:9324 sqs send-message --queue-url "$Q" --message-body "$body" \
      --message-attributes '{"type":{"DataType":"String","StringValue":"JobLibrary\\Job\\Promotion\\DepositJob"},"Content-Type":{"DataType":"String","StringValue":"application/json"}}' >/dev/null
  done; }
left(){ aws --endpoint-url http://localhost:9324 sqs get-queue-attributes --queue-url "$Q" --attribute-names ApproximateNumberOfMessages --query 'Attributes.ApproximateNumberOfMessages' --output text; }
consume(){ # consume <expected messages>; retried until the queue is empty, so a slow long-poll never leaves a copy behind
  for _ in 1 2 3; do
    docker exec promotion.php php bin/console messenger:consume promotion_sqs --limit="$1" --time-limit=20 2>&1 | grep -i -e "error\|exception" || true
    [ "$(left)" = "0" ] && break; echo "queue still has $(left) message(s), consuming again"
  done; echo "consumed; queue left: $(left)"; }
sql(){ docker exec "$1" php bin/console dbal:run-sql "$2"; }
FAILED=0
newman_part(){ local env=$1; shift   # a failing part does not stop the run: the later folders are still worth seeing
  npx -y newman run CLS-3676.postman_collection.json -e "$env" --export-environment "$env" \
    --env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC" \
    --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW" \
    --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC" \
    --env-var "username=casino+casino@gmail.com" --env-var "password=$PW" --env-var "guardKey=$GK" "$@" || FAILED=1; }

aws --endpoint-url http://localhost:9324 sqs purge-queue --queue-url "$Q" >/dev/null   # no leftover from an aborted run
E=$(mktemp -d)/env.json; echo '{"name":"run","values":[]}' > "$E"
newman_part "$E" --folder "0 Precondition: player withdrawable not negative" --folder "1 BO setup" --folder "2 GW player opts in"

push $((TX+1)) success 2; consume 2                       # cells 1, 11: same deposit delivered twice
newman_part "$E" --folder "3 BO verify: tx1 delivered twice -> each configuration rewarded once (cells 1, 11)"

push $((TX+2)) success; consume 1                         # cell 12: a distinct deposit
newman_part "$E" --folder "4 BO verify: tx2 (distinct deposit) -> rewarded again (cell 12)"

push $((TX+3)) initiated; push $((TX+3)) pending; push $((TX+3)) success; consume 3   # cell 13
newman_part "$E" --folder "5 BO verify: tx3 initiated, pending, success -> rewarded (cell 13)"

push $((TX+4)) initiated; push $((TX+5)) success; push $((TX+4)) success; consume 3   # cell 13a
newman_part "$E" --folder "6 BO verify: tx4 initiated, tx5 success, tx4 success -> both rewarded (cell 13a)"

newman_part "$E" --folder "7 claim twice: 409 on the second (cells 17, 18, 19)"

# DEV-ONLY read: the promotion events behind the counts. No wallet read: wallet keys sub_balance by bonus id, and
# promotion's bonus ids restart after every make init, so a local wallet read mixes rows from earlier runs.
PA=$(jq -r '.values[]|select(.key=="pcA").value' "$E"); PB=$(jq -r '.values[]|select(.key=="pcB").value' "$E")
echo "== promotion events of A ($PA) and B ($PB):"
sql promotion.php "SELECT p.promotion_configuration_id AS pc, p.id AS promotion, p.status, e.event_name, e.transaction_id FROM promotion p LEFT JOIN promotion_event e ON e.promotion_id = p.id WHERE p.promotion_configuration_id IN ($PA,$PB) ORDER BY p.id, e.id"
exit $FAILED
