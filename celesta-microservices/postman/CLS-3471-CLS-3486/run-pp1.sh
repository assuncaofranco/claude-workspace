#!/usr/bin/env bash
# Runs the collection against preprod-1. Credentials come from the vault at run time.
# Usage: ./run-pp1.sh <domainId> <playerId> ["YYYY-MM-DD HH:MM:SS" from, UTC]
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-preprod.md
bo(){ sed -n '1,25p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
npx -y newman run CLS-3471-CLS-3486.postman_collection.json \
  --env-var "BO_baseUrl=$(bo BO_baseUrl)" \
  --env-var "domainId=$1" --env-var "playerId=$2" --env-var "testFrom=${3:-}" \
  --env-var "BO_oauth_client_id=$(bo BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(bo BO_oauth_client_secret)" \
  --env-var "BO_username=$(bo BO_username)" --env-var "BO_password=$(bo BO_password)"
