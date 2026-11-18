#!/bin/bash
# Gera o OpenAPI de um ref (branch, commit, origin/master) sem tocar em nenhuma stack.
# Exporta o ref para um diretório temporário e roda o gerador do `make openapi` num container
# descartável (imagem do serviço php do compose), com vendor/ e bin/ do clone principal só leitura.
# `make openapi` não serve aqui: roda no container da stack, que está montada num checkout
# qualquer — outra sessão pode estar usando — e mostraria a árvore errada.
#   ./openapi-ref.sh <serviço> <ref> <saída.json>
# Só serviços PHP (o Makefile chama bin/openapi). Go e demais: sai com 3, sem gerar.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
SVC="$(resolve_service "${1:-}")" || exit 1
REF="${2:-}"; OUT="${3:-}"
[ -n "$REF" ] && [ -n "$OUT" ] || die "uso: openapi-ref.sh <serviço> <ref> <saída.json>"
DIR="$(service_dir "$SVC")"

CMD="$(make -C "$DIR" -n openapi 2>/dev/null | grep -m1 'bin/openapi' | sed -E 's/.*exec php //; s/ -o [^ ]+//')"
[ -n "$CMD" ] || { echo "$SVC: o Makefile não usa bin/openapi (não é PHP): gerador não suportado" >&2; exit 3; }

IMG="$(cd "$DIR" && docker compose -f docker-compose.dev.yml config --format json | jq -r '.services.php.image')"
[ -n "$IMG" ] && [ "$IMG" != null ] || die "$SVC: imagem do serviço php não encontrada no compose"
[ -d "$DIR/vendor" ] && [ -d "$DIR/bin" ] || die "$SVC: sem vendor/ ou bin/ no clone principal (make init)"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
git -C "$DIR" archive "$REF" | tar -x -C "$TMP" || die "$SVC: ref $REF não existe"

# o comando do Makefile está em sh: precisa de sh -c para --processor com barras
docker run --rm -v "$TMP":/var/www/app -v "$DIR/vendor":/var/www/app/vendor:ro \
  -v "$DIR/bin":/var/www/app/bin:ro -w /var/www/app "$IMG" sh -c "$CMD" > "$OUT" \
  || die "$SVC@$REF: o gerador falhou"
jq -e .paths "$OUT" >/dev/null || die "$SVC@$REF: saída não é um OpenAPI"
done_ "$SVC@$REF → $OUT"
