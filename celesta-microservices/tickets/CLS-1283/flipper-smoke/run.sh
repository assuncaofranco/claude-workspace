#!/usr/bin/env bash
# Runs the collection against local dev. Credentials come from the vault at run time.
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-dev.md
val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
CID=$(val client_id); CSEC=$(val client_secret)
PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
npx -y newman run "${COLLECTION:-CLS-1283-flipper-smoke.postman_collection.json}" \
  --env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC" \
  --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW" \
  --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC" \
  --env-var "username=casino+casino@gmail.com" --env-var "password=$PW" \
  "$@"
