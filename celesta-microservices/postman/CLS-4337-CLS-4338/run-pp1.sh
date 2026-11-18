#!/usr/bin/env bash
# Runs the pp1 collection. Credentials come from the vault at run time.
# Usage: ./run-pp1.sh setup                    folders 1-3, prints the game url and testFrom
#        ./run-pp1.sh verify "<testFrom>" "<eurRealBefore>"   folder 4, after playing the free rounds
set -euo pipefail
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-preprod.md
bo(){ sed -n '1,25p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
gw(){ sed -n '26,40p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
creds=(
  --env-var "BO_baseUrl=$(bo BO_baseUrl)" --env-var "baseUrl=$(gw baseUrl)"
  --env-var "BO_oauth_client_id=$(bo BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(bo BO_oauth_client_secret)"
  --env-var "BO_username=$(bo BO_username)" --env-var "BO_password=$(bo BO_password)"
  --env-var "oauth_client_id=$(gw oauth_client_id)" --env-var "oauth_client_secret=$(gw oauth_client_secret)"
  --env-var "username=$(gw username)" --env-var "password=$(gw password)"
)
C=CLS-4337-CLS-4338.pp1.postman_collection.json
case "${1:-}" in
  setup)
    npx -y newman run "$C" "${creds[@]}" \
      --folder "1 BO: USD free-round bonus offered to the EUR player" \
      --folder "2 GW: player claims it and launches the CGA game in EUR" \
      --folder "3 BO: claim created the USD wallet" ;;
  verify)
    npx -y newman run "$C" "${creds[@]}" --env-var "testFrom=$2" --env-var "eurRealBefore=$3" \
      --folder "4 BO verify (after playing the free rounds)" ;;
  *) echo "usage: $0 setup | verify <testFrom> <eurRealBefore>"; exit 1 ;;
esac
