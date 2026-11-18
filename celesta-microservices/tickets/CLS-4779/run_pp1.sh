#!/usr/bin/env bash
# CLS-4779 on preprod-1. Credentials come from the vault at run time, never from the collection.
# Usage: ./run_pp1.sh                 whole collection
#        ./run_pp1.sh --folder "1 Player: Paytech card deposit"
set -euo pipefail
cd "$(dirname "$0")"
python3 -I gen_pp1.py
V=~/.claude-secrets/celesta-preprod.md
val(){ sed -n '1,/^## preprod-2/p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
npx -y newman run CLS-4779.pp1.postman_collection.json \
  --env-var "BO_oauth_client_id=$(val BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(val BO_oauth_client_secret)" \
  --env-var "BO_username=$(val BO_username)" --env-var "BO_password=$(val BO_password)" \
  --env-var "oauth_client_id=$(val oauth_client_id)" --env-var "oauth_client_secret=$(val oauth_client_secret)" \
  --env-var "username=$(val username)" --env-var "password=$(val password)" \
  --env-var "seonSession=$(val seonSession)" "$@"
