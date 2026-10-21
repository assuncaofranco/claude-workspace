#!/usr/bin/env bash
# ./run.sh          local dev
# ./run.sh pp1      preprod-1 (gateway + BO only, no internal service)
# Credentials come from the vault at run time; extra args go to newman.
set -euo pipefail
cd "$(dirname "$0")"
ARGS=()
if [[ "${1:-}" == pp1 ]]; then
  shift
  # every "| `var` | `value` |" row of the preprod vault is a collection variable
  while IFS=$'\t' read -r k v; do ARGS+=(--env-var "$k=$v"); done < <(
    grep -E '^\| `[A-Za-z_]+` \| `[^`]*` \|' ~/.claude-secrets/celesta-preprod.md | awk -F'`' '{print $2"\t"$4}')
else
  V=~/.claude-secrets/celesta-dev.md
  val(){ grep -m1 "| \`$1\`" "$V" | awk -F'`' '{print $4}'; }
  CID=$(val client_id); CSEC=$(val client_secret)
  PW=$(grep -m1 'seeded têm senha' "$V" | awk -F'`' '{print $2}')
  ARGS=(--env-var "BO_oauth_client_id=$CID" --env-var "BO_oauth_client_secret=$CSEC"
    --env-var "BO_username=owner@gmail.com" --env-var "BO_password=$PW"
    --env-var "oauth_client_id=$CID" --env-var "oauth_client_secret=$CSEC"
    --env-var "username=casino+casino@gmail.com" --env-var "password=$PW")
fi
npx -y newman run CLS-3835.postman_collection.json "${ARGS[@]}" "$@"
