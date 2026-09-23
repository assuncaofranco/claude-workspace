#!/bin/bash
# Roda os testes do serviço dentro do container (o Makefile já encapsula o docker).
#   ./test.sh <serviço>
# O phpunit escreve em var/log/phpunit.log — o script mostra o fim do arquivo,
# porque `make test` redireciona e não imprime nada na falha.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
SVC="$(resolve_service "${1:-}")" || exit 1
DIR="$(service_dir "$SVC")"
step "$SVC: make test"
if ( cd "$DIR" && make test ); then
  done_ "testes passaram"
else
  echo "${RED}testes falharam${OFF}"
fi
LOG="$DIR/var/log/phpunit.log"
[ -f "$LOG" ] && { echo; echo "${DIM}—— fim de var/log/phpunit.log${OFF}"; tail -25 "$LOG"; }
