#!/bin/bash
# Liga este repositório ao ~/.claude de uma máquina.
#
# Idempotente: rodar de novo repara o que estiver faltando e não toca no resto.
# `--check` não escreve nada, só relata.
#
#   ./bootstrap.sh            monta ou repara
#   ./bootstrap.sh --check    verifica e sai != 0 se algo estiver quebrado

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE="${CLAUDE_HOME:-$HOME/.claude}"
VAULT="$HOME/.claude-secrets"
CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; DIM=$'\033[2m'; OFF=$'\033[0m'
problems=0

say()  { printf '  %s%-52s%s %s\n' "$DIM" "$1" "$OFF" "$2"; }
ok()   { say "$1" "${GREEN}ok${OFF}"; }
fix()  { say "$1" "${YELLOW}$2${OFF}"; }
bad()  { say "$1" "${RED}$2${OFF}"; problems=$((problems+1)); }

# Um symlink de DIRETÓRIO. Nunca de arquivo — arquivo quebra quando um editor
# escreve num temporário e renomeia por cima.
link_dir() {
  local link="$1" target="$2" label="$3"

  if [ ! -d "$target" ]; then
    bad "$label" "alvo não existe: $target"
    return
  fi

  if [ -L "$link" ]; then
    local current
    current="$(readlink "$link")"
    if [ "$current" = "$target" ]; then
      ok "$label"
    else
      bad "$label" "aponta para outro lugar: $current"
    fi
    return
  fi

  if [ -e "$link" ]; then
    # Existe conteúdo real onde deveria haver link. Nunca apagar sozinho.
    bad "$label" "existe como diretório real — mover o conteúdo para o repo antes"
    return
  fi

  if [ "$CHECK" = 1 ]; then
    bad "$label" "faltando"
  else
    mkdir -p "$(dirname "$link")"
    ln -s "$target" "$link" && fix "$label" "criado"
  fi
}

echo
echo "  repositório : $REPO"
echo "  ~/.claude   : $CLAUDE"
echo

echo "  ${DIM}symlinks de diretório${OFF}"
link_dir "$CLAUDE/commands" "$REPO/global/skills"                       "commands -> global/skills"
link_dir "$CLAUDE/memory"   "$REPO/global/memory"                       "memory -> global/memory"
link_dir "$CLAUDE/shared"   "$REPO/celesta-microservices/shared"        "shared -> celesta-microservices/shared"
link_dir "$CLAUDE/postman"  "$REPO/celesta-microservices/postman"       "postman -> celesta-microservices/postman"
link_dir "$CLAUDE/projects/-Users-l-franco-Desktop-celesta-projects/memory" \
         "$REPO/celesta-microservices/memory" "memória do projeto celesta"
link_dir "$CLAUDE/projects/-Users-l-franco-Desktop-infra/memory" \
         "$REPO/celesta-infra/memory"         "memória do projeto infra"

echo
echo "  ${DIM}stub de CLAUDE.md${OFF}"
STUB="$CLAUDE/CLAUDE.md"
if [ -f "$STUB" ] && grep -q "claude-workspace/global/CLAUDE.md" "$STUB" 2>/dev/null; then
  ok "CLAUDE.md importa do repositório"
elif [ "$CHECK" = 1 ]; then
  bad "CLAUDE.md" "não importa do repositório"
else
  [ -f "$STUB" ] && cp "$STUB" "$STUB.pre-bootstrap"
  cat > "$STUB" <<EOF
# Instruções globais

Este arquivo é um stub. O conteúdo real é versionado em \`$REPO\` e entra por import.

@$REPO/global/CLAUDE.md
@$REPO/global/RTK.md
@$REPO/celesta-microservices/CLAUDE.md

Para montar tudo numa máquina nova: \`$REPO/bootstrap.sh\`.
EOF
  fix "CLAUDE.md" "escrito (o anterior ficou em CLAUDE.md.pre-bootstrap)"
fi

echo
echo "  ${DIM}plugin do SDD (vem do marketplace, não é versionado aqui)${OFF}"
PLUGIN="celesta-engineering-playbook@celesta-claude-marketplace"
if grep -q "\"$PLUGIN\"" "$CLAUDE/plugins/installed_plugins.json" 2>/dev/null; then
  ok "$PLUGIN"
elif [ "$CHECK" = 1 ]; then
  bad "$PLUGIN" "não instalado"
elif ! command -v claude >/dev/null; then
  bad "$PLUGIN" "não instalado e o CLI claude não está no PATH"
else
  claude plugin marketplace add celesta-tech/celesta-claude-marketplace >/dev/null 2>&1
  if claude plugin install "$PLUGIN" >/dev/null 2>&1; then
    fix "$PLUGIN" "instalado"
  else
    bad "$PLUGIN" "falhou — o gh precisa ler celesta-tech/celesta-claude-marketplace"
  fi
fi

echo
echo "  ${DIM}vault de segredos (fora do git, nunca versionado)${OFF}"
if [ -d "$VAULT" ]; then
  perm="$(stat -f '%Lp' "$VAULT" 2>/dev/null || stat -c '%a' "$VAULT" 2>/dev/null)"
  if [ "$perm" = "700" ]; then
    ok "~/.claude-secrets ($(ls -1 "$VAULT" | wc -l | tr -d ' ') arquivos)"
  else
    if [ "$CHECK" = 1 ]; then
      bad "~/.claude-secrets" "permissão $perm, deveria ser 700"
    else
      chmod 700 "$VAULT" && fix "~/.claude-secrets" "permissão corrigida para 700"
    fi
  fi
else
  bad "~/.claude-secrets" "não existe — as skills vão pedir credencial que não está em lugar nenhum"
fi

echo
echo "  ${DIM}hook de pre-commit${OFF}"
HOOKS_PATH="$(git -C "$REPO" config --local core.hooksPath 2>/dev/null)"
if [ "$HOOKS_PATH" = ".githooks" ]; then
  ok "core.hooksPath = .githooks"
elif [ "$CHECK" = 1 ]; then
  bad "core.hooksPath" "não aponta para .githooks — o scan de segredo não roda"
else
  git -C "$REPO" config --local core.hooksPath .githooks && fix "core.hooksPath" "configurado"
fi
chmod +x "$REPO/.githooks/pre-commit" 2>/dev/null

echo
echo "  ${DIM}identidade do git (conta pessoal, não a da empresa)${OFF}"
email="$(git -C "$REPO" config --local user.email 2>/dev/null)"
if [ -n "$email" ]; then
  ok "user.email = $email"
else
  bad "user.email" "não configurado localmente — os commits vão sair com a identidade global"
fi

echo
if [ "$problems" -gt 0 ]; then
  echo "  ${RED}$problems problema(s).${OFF}"
  [ "$CHECK" = 1 ] && echo "  Rodar sem --check repara o que for reparável automaticamente."
  echo
  exit 1
fi
echo "  ${GREEN}tudo de pé.${OFF}"
echo
