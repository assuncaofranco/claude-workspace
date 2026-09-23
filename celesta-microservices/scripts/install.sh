#!/bin/bash
# Sobe o serviço do zero e deixa pronto para trabalhar.
#   ./install.sh <serviço>     ou, de dentro do repositório do serviço, ./install.sh
#
# Roda make init, build e openapi na ordem, pulando o que aquele serviço não tem.
# O `make init` é obrigatório depois de troca grande de branch: cache de Doctrine e
# banco de teste velhos produzem erro que parece regressão e não é.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
SVC="$(resolve_service "${1:-}")" || exit 1
echo "${DIM}serviço:${OFF} $SVC"
run_make "$SVC" init
run_make "$SVC" build
run_make "$SVC" openapi
echo; done_ "$SVC pronto."
