#!/bin/bash
# Lista as sessões do Claude Code de um dia: horário, tickets citados e as mensagens do usuário.
# Matéria-prima da skill `daily`; o resumo é ela que faz.
#
#   daily-log.sh              último dia útil (segunda → sexta anterior)
#   daily-log.sh 2026-10-13   dia específico, no fuso local

set -uo pipefail

if [ -n "${1:-}" ]; then
  DAY="$1"
elif [ "$(date +%u)" = 1 ]; then
  DAY="$(date -v-3d +%F)"
else
  DAY="$(date -v-1d +%F)"
fi

echo "# dia $DAY"

# Timestamp do transcript é UTC; o dia é o local.
local_day='(.timestamp // "") | sub("\\.[0-9]+Z$"; "Z") | try (fromdate | localtime | strftime("%Y-%m-%d")) catch ""'

# Só o nível de cima: subagents/ repetiriam a mesma sessão.
find "$HOME/.claude/projects" -maxdepth 2 -name '*.jsonl' -newermt "$DAY" 2>/dev/null | while read -r f; do
  msgs="$(jq -r --arg d "$DAY" "
    select(.type == \"user\" and (.isMeta | not) and (($local_day) == \$d))
    | .message.content
    | if type == \"string\" then . else (map(select(.type == \"text\") | .text) | join(\" \")) end
    | select(test(\"^<(command-|local-command-|system-reminder)\") | not)
    | select(test(\"^\\\\[Request interrupted\") | not)
    | gsub(\"\\\\s+\"; \" \") | select(length > 1) | .[0:300]
  " "$f" 2>/dev/null)"
  [ -z "$msgs" ] && continue

  span="$(jq -r --arg d "$DAY" "select(($local_day) == \$d) | .timestamp
    | sub(\"\\\\.[0-9]+Z$\"; \"Z\") | fromdate | localtime | strftime(\"%H:%M\")" "$f" 2>/dev/null | sort | sed -n '1p;$p' | paste -sd- -)"
  tickets="$(grep -oE '(CLS|CEL|QAA)-[0-9]+' "$f" | sort | uniq -c | sort -rn | head -5 | awk '{print $2"("$1")"}' | paste -sd' ' -)"

  echo
  echo "## $(basename "$(dirname "$f")") $(basename "$f" .jsonl)  $span"
  echo "tickets: ${tickets:-nenhum}"
  echo "$msgs" | sed 's/^/- /'
done
