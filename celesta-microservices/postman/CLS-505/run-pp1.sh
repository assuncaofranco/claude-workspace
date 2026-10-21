#!/usr/bin/env bash
# Runs one collection against preprod-1 (or PP=2 for preprod-2), skipping DEV-ONLY folders. Credentials come from the vault.
# Usage: [PP=2] ./run-pp1.sh <game|contact|cms|promotion> [newman args]
set -euo pipefail
PP=${PP:-1}
export PATH="$HOME/.npm-global/bin:$PATH"
cd "$(dirname "$0")"
V=~/.claude-secrets/celesta-preprod.md
bo(){ sed -n '1,25p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
gw(){ sed -n '26,40p' "$V" | grep -m1 "| \`$1\`" | awk -F'`' '{print $4}'; }
case "${1:?game|contact|cms|promotion}" in
  game)    C=CLS-3288-game; F=(--folder "1 GW launch Relax game" --folder "2 Relax webhooks: bet, win, bet + rollback (provider callback)" --folder "3 BO game reads" --folder "4 Free rounds grant + cancel (promotion -> game)")
           X=(--env-var "gameUrl=https://game.preprod-$PP.octopodev.com" --env-var "gameId=55672" --env-var "externalGameId=moneytrain3" --env-var "gameGatewayId=41" --env-var "gameStudioId=562") ;;
  contact) C=CLS-3290-contact; F=(); X=() ;;
  cms)     C=CLS-3291-cms; F=(--folder "1 BO content tag" --folder "2 BO content block" --folder "3 BO terms and conditions (draft only, never publish on a shared domain)" --folder "4 BO custom email template" --folder "6 BO cleanup"); X=() ;;
  promotion) C=CLS-3289-promotion; F=(--folder "0 BO setup: segment" --folder "1 BO promotion tags" --folder "2 BO reward configuration" --folder "3 BO promotion configuration + tags" --folder "4 BO weekly schedule" --folder "5 BO reward aggregator" --folder "6 offer free bonus to player, GW lists it, BO cancels" --folder "7 BO cleanup"); X=() ;;
  *) exit 1 ;;
esac
shift
case " $* " in *" --folder "*) F=() ;; esac
newman run "$C.postman_collection.json" ${F[@]+"${F[@]}"} ${X[@]+"${X[@]}"} \
  --env-var "BO_baseUrl=$(bo BO_baseUrl | sed "s/preprod-1/preprod-$PP/")" --env-var "baseUrl=$(gw baseUrl | sed "s/preprod-1/preprod-$PP/")" --env-var "domainId=56" \
  --env-var "BO_oauth_client_id=$(bo BO_oauth_client_id)" --env-var "BO_oauth_client_secret=$(bo BO_oauth_client_secret)" \
  --env-var "BO_username=$(bo BO_username)" --env-var "BO_password=$(bo BO_password)" \
  --env-var "oauth_client_id=$(gw oauth_client_id)" --env-var "oauth_client_secret=$(gw oauth_client_secret)" \
  --env-var "username=$(gw username)" --env-var "password=$(gw password)" \
  "$@"
