#!/bin/bash
# Base comum dos scripts. Lê context.yaml para não repetir o que é dado.
# Sem dependência de yq — o parse é o mínimo necessário para as chaves que usamos.

set -uo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT="$SCRIPTS_DIR/../context.yaml"
PROJECTS_ROOT="${CELESTA_ROOT:-$HOME/Desktop/celesta-projects}"

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; DIM=$'\033[2m'; OFF=$'\033[0m'

die()  { echo "${RED}erro:${OFF} $*" >&2; exit 1; }
step() { echo; echo "${DIM}——${OFF} ${YELLOW}$*${OFF}"; }
done_() { echo "${GREEN}✓${OFF} $*"; }

# Lista os serviços declarados no context.yaml.
list_services() {
  awk '/^services:/{f=1;next} f&&/^[a-z]/{exit} f&&/^  [a-z]/{gsub(/:.*/,"");gsub(/ /,"");print}' "$CONTEXT"
}

# Alvos de make que aquele serviço realmente tem.
service_make_targets() {
  awk -v s="$1" '
    /^services:/{f=1;next}
    f&&/^[a-z]/{exit}
    f&&$0 ~ "^  "s":" {
      if (match($0, /make: \[[^]]*\]/)) {
        t = substr($0, RSTART+7, RLENGTH-8); gsub(/ /,"",t); gsub(/,/,"\n",t); print t
      }
      exit
    }' "$CONTEXT"
}

has_target() {
  service_make_targets "$1" | grep -qx "$2"
}

# Resolve o argumento para um diretório de serviço: aceita o nome completo, um
# sufixo (`wallet`), ou nada quando já se está dentro do repositório do serviço.
resolve_service() {
  local arg="${1:-}"

  case "$arg" in
    -h|--help)
      echo "Uso: $(basename "$0") <serviço>" >&2
      echo "  Aceita o nome completo (celesta-wallet), um sufixo (wallet)," >&2
      echo "  ou nada quando você já está dentro do repositório do serviço." >&2
      echo >&2
      echo "  Serviços: $(list_services | tr '\n' ' ')" >&2
      exit 0 ;;
  esac

  if [ -z "$arg" ]; then
    local d="$PWD"
    while [ "$d" != "/" ]; do
      local base; base="$(basename "$d")"
      if list_services | grep -qx -- "$base"; then echo "$base"; return 0; fi
      d="$(dirname "$d")"
    done
    die "nenhum serviço informado e o diretório atual não é um. Uso: $(basename "$0") <serviço>"
  fi

  if list_services | grep -qx -- "$arg"; then echo "$arg"; return 0; fi

  local matches; matches="$(list_services | grep -- "$arg" || true)"
  local n; n="$(echo "$matches" | grep -c . || true)"
  case "$n" in
    1) echo "$matches" ;;
    0) die "serviço desconhecido: $arg" ;;
    *) die "ambíguo: '$arg' bate com $(echo "$matches" | tr '\n' ' ')" ;;
  esac
}

service_dir() {
  local d="$PROJECTS_ROOT/$1"
  [ -d "$d" ] || die "diretório não encontrado: $d"
  echo "$d"
}

# Roda um alvo de make no serviço, pulando em silêncio o que não existe ali.
run_make() {
  local svc="$1" target="$2" dir
  dir="$(service_dir "$svc")"

  if ! has_target "$svc" "$target"; then
    echo "${DIM}   (pulado: $svc não tem 'make $target')${OFF}"
    return 0
  fi

  step "$svc: make $target"
  ( cd "$dir" && make "$target" ) || die "'make $target' falhou em $svc"
  done_ "make $target"
}
