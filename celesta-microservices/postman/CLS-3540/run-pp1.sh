#!/usr/bin/env bash
# Runs the collection against preprod-1 (PP=2 for preprod-2). Credentials come from the vault.
# Usage: [PP=2] ./run-pp1.sh [newman args]
set -euo pipefail
PP=${PP:-1}
export PATH="$HOME/.npm-global/bin:$PATH"
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-preprod.md
bo(){ sed -n '1,25p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
gw(){ sed -n '26,40p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
python3 -I gen.py
newman run CLS-3540.postman_collection.json \
  --env-var "BO_baseUrl=$(bo BO_baseUrl | sed "s/preprod-1/preprod-$PP/")" --env-var "baseUrl=$(gw baseUrl | sed "s/preprod-1/preprod-$PP/")" --env-var "domainId=56" \
  --env-var "BO_oauth_client_id=$(bo BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(bo BO_oauth_client_secret)" \
  --env-var "BO_username=$(bo BO_username)" --env-var "BO_password=$(bo BO_password)" \
  --env-var "oauth_client_id=$(gw oauth_client_id)" --env-var "oauth_client_secret=$(gw oauth_client_secret)" \
  --env-var "username=$(gw username)" --env-var "password=$(gw password)" \
  "$@"
