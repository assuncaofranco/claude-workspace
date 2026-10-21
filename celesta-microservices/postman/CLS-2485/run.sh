#!/usr/bin/env bash
# Local dev only. Credentials come from the vault at run time.
# Locally nothing consumes the queues, so promotion's promotion_bonus_sqs worker is run by hand
# between the parts, and wallet's application 1 is marked sportsbook only for the run.
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-dev.md
val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
CID=$(val client_id); CSEC=$(val client_secret)
PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
sql(){ docker exec wallet.php php bin/console dbal:run-sql "$1"; }
consume(){ docker exec promotion.php php bin/console messenger:consume promotion_bonus_sqs --time-limit=20 -q || true; }
newman_part(){ local env=$1; shift
  npx -y newman run CLS-2485.postman_collection.json -e "$env" --export-environment "$env" \
    --env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC" \
    --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW" \
    --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC" \
    --env-var "username=casino+casino@gmail.com" --env-var "password=$PW" "$@"; }

# application 1 has vertical NULL in dev; mark it sportsbook for the run and put NULL back
sql "UPDATE application SET vertical = '[\"casino\",\"sb\"]' WHERE domain_id = 1" >/dev/null
trap 'sql "UPDATE application SET vertical = NULL WHERE domain_id = 1" >/dev/null' EXIT
docker exec wallet.php php bin/console cache:pool:clear cache.app -q || true

E=$(mktemp -d)/env.json; echo '{"name":"run","values":[]}' > "$E"
newman_part "$E" --folder "0 Precondition: player 1 withdrawable not negative" --folder "1 BO setup" --folder "2 GW player claims both" --folder "3 DEV-ONLY sportsbook bonus bet (wallet, SB provider side)"
consume
newman_part "$E" --folder "4 BO verify played (after promotion consumed Depleted)" --folder "5 DEV-ONLY sportsbook rollback (wallet, SB provider side)"
consume
newman_part "$E" --folder "6 BO verify claimed again (after promotion consumed Restored)" --folder "7 BO cancel bonus C"

# DEV-ONLY: wallet side of the BO cancel (sub_balance id == promotion bonus id, CEL-6848)
BC=$(jq -r '.values[]|select(.key=="bonusC").value' "$E")
echo "wallet sub_balance for bonus C ($BC):"; sql "SELECT bonus_id, status, total_balance FROM sub_balance WHERE bonus_id = $BC"
