#!/usr/bin/env bash
# Runs one collection against local dev. Credentials come from the vault, the guard key from cms .env.dev.
# Usage: ./run.sh <game|contact|cms|promotion> [newman args]
set -euo pipefail
export PATH="$HOME/.npm-global/bin:$PATH"
cd "$(dirname "$0")"
case "${1:?game|contact|cms|promotion}" in
  game) C=CLS-3288-game ;; contact) C=CLS-3290-contact ;; cms) C=CLS-3291-cms ;; promotion) C=CLS-3289-promotion ;; *) exit 1 ;;
esac
shift
V=~/.claude-secrets/celesta-dev.md
val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
CID=$(val client_id); CSEC=$(val client_secret)
PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
GK=$(grep -m1 '^GUARD_KEY=' ~/Desktop/celesta-projects/celesta-cms/.env.dev | cut -d= -f2-)
newman run "$C.postman_collection.json" \
  --env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC" \
  --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW" \
  --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC" \
  --env-var "username=casino+casino@gmail.com" --env-var "password=$PW" \
  --env-var "guardKey=$GK" \
  "$@"
