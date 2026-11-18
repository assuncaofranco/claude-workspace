#!/usr/bin/env bash
# Runs the collection against local dev. The guard key comes from the wallet container.
set -euo pipefail
cd "$(dirname "$0")"
npx -y newman run CLS-4337-CLS-4338.postman_collection.json \
  --env-var "guardKey=$(docker exec wallet.php printenv GUARD_KEY)" "$@"
