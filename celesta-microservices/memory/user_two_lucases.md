---
name: user-two-lucases
description: "Há dois Lucas: o usuário é Lucas Franco (l.franco@celesta.io, dev backend); Lucas Azevedo é o team leader de DevOps, novo na empresa em 2026-09 — autor dos commits de infra em celesta-argocd. Nunca atribuir commits de infra ao usuário pelo primeiro nome."
metadata: 
  node_type: memory
  type: user
  originSessionId: ac86a1f1-7cb7-43de-b034-de3b1dcd6c74
  modified: 2026-09-22T09:58:30.994Z
---

O usuário é **Lucas Franco** (l.franco@celesta.io), dev backend nos serviços Celesta.

**Lucas Azevedo** é outra pessoa: team leader de DevOps, novo na empresa (set/2026). Assina os
commits do `celesta-argocd` (ex.: CEL-9270, 2026-09-16, captura de logs no nginx do game).

**Why:** em 2026-09-22 atribuí os commits CEL-9270 ao usuário ("seus commits") só pelo primeiro nome
no `git log`; ele corrigiu. Franco levantou a hipótese de Azevedo ter adicionado a captura de body
sem querer por ser novo — o `git blame` mostrou que **não**: `lua_need_request_body` e o
`log_format` com `$request_body`/`$resp_body` são de Artem P, 2024-03-28 (CELB-1259); Azevedo só
endureceu a captura em 2026-09-16 (cap de 1000 chars, merge dos maps, omissão de headers com
credencial). Levar a questão do body a ele como continuação do CEL-9270, não como erro dele.

**How to apply:** ao citar autor de commit, usar nome completo do `git log --format=%an` e não inferir
que "Lucas" = usuário. Relacionado: `global/rules/writing.md`.
