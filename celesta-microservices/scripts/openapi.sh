#!/bin/bash
# Regenera public/open-api.json. Nenhum serviço versiona esse arquivo, então ele
# precisa ser gerado antes de montar uma coleção (passo 6) e de novo depois de
# implementar (passo 8) — a anotação do que o ticket cria só produz saída com o código lá.
#   ./openapi.sh <serviço>
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
SVC="$(resolve_service "${1:-}")" || exit 1
run_make "$SVC" openapi
echo "${DIM}gerado em $(service_dir "$SVC")/public/open-api.json${OFF}"
