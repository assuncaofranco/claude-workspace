#!/usr/bin/env bash
# Local dev only. Credentials come from the vault at run time.
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-dev.md
val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
CID=$(val client_id); CSEC=$(val client_secret)
PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
GK=$(grep -m1 'GUARD_KEY=' "$V" | sed -E 's/.*GUARD_KEY=([a-z]+).*/\1/')
Q=http://localhost:9324/000000000000/dev-promotion
export AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x AWS_DEFAULT_REGION=eu-west-1
TX=$(date +%s); TXA=$((TX+1)); TXB=$((TX+2))

python3 -I gen.py
E=$(mktemp -d)/env.json
cat > "$E" <<JSON
{"name":"run","values":[
 {"key":"BO_baseUrl","value":"http://localhost:84"},{"key":"baseUrl","value":"http://localhost:93"},
 {"key":"promotionUrl","value":"http://localhost:99"},{"key":"domainId","value":"1"},
 {"key":"playerA","value":"1"},{"key":"playerB","value":"27"},
 {"key":"userA","value":"casino+casino@gmail.com"},{"key":"userB","value":"customer_casino_deposit@gmail.com"},
 {"key":"txA","value":"$TXA"},{"key":"txB","value":"$TXB"}]}
JSON
run(){ npx -y newman run CLS-4314.postman_collection.json -e "$E" --export-environment "$E" \
  --env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC" \
  --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW" \
  --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC" --env-var "password=$PW" \
  --env-var "guardKey=$GK" "$@"; }

run --folder "1 Setup: one deposit tier per currency, each player opts in"

push(){ # push <playerId> <transactionId> <currency>
  local body; body=$(printf '{"playerId":%s,"domainId":1,"transactionId":%s,"status":"success","amount":50.0,"currency":"%s","rewardIds":null}' "$1" "$2" "$3")
  aws --endpoint-url http://localhost:9324 sqs send-message --queue-url "$Q" --message-body "$body" \
    --message-attributes '{"type":{"DataType":"String","StringValue":"JobLibrary\\Job\\Promotion\\DepositJob"},"Content-Type":{"DataType":"String","StringValue":"application/json"}}' >/dev/null; }
push 1 "$TXA" EUR
push 27 "$TXB" CAD
left(){ aws --endpoint-url http://localhost:9324 sqs get-queue-attributes --queue-url "$Q" --attribute-names ApproximateNumberOfMessages --query 'Attributes.ApproximateNumberOfMessages' --output text; }
for _ in 1 2 3 4 5; do
  docker exec promotion.php php bin/console messenger:consume promotion_sqs --limit=50 --time-limit=20 2>&1 | grep -i -e "error\|exception" || true
  [ "$(left)" = "0" ] && break
done
echo "queue left: $(left)"
echo "deposits consumed: txA=$TXA (player 1), txB=$TXB (player 27)"

run --folder "2 Compare per-player and domain routes"
