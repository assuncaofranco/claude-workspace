#!/bin/bash
# phpinsights nos thresholds do serviço (shared/coding-standards.md).
#   ./lint.sh <serviço>
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
SVC="$(resolve_service "${1:-}")" || exit 1
run_make "$SVC" lint
