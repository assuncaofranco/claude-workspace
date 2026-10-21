#!/usr/bin/env bash
# Runs the collection against preprod-1. Credentials come from the vault at run time.
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-preprod.md
bo(){ sed -n '1,25p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
gw(){ sed -n '26,40p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
npx -y newman run CLS-2851.postman_collection.json \
  --env-var "BO_baseUrl=$(bo BO_baseUrl)" --env-var "baseUrl=$(gw baseUrl)" \
  --env-var "gameUrl=https://game.preprod-1.octopodev.com" \
  --env-var "domainId=56" --env-var "gameId=55672" --env-var "externalGameId=moneytrain3" \
  --env-var "gameGatewayId=41" --env-var "gameStudioId=562" \
  --env-var "BO_oauth_client_id=$(bo BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(bo BO_oauth_client_secret)" \
  --env-var "BO_username=$(bo BO_username)" --env-var "BO_password=$(bo BO_password)" \
  --env-var "oauth_client_id=$(gw oauth_client_id)" --env-var "oauth_client_secret=$(gw oauth_client_secret)" \
  --env-var "username=$(gw username)" --env-var "password=$(gw password)" \
  "$@"
