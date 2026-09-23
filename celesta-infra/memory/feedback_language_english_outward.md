---
name: feedback-language-english-outward
description: "Tudo que não for conversa entre nós dois vai em inglês — PR, comentário, commit, ticket, Slack"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-16T10:18:13.445Z
---

Conversa entre nós dois: português. **Todo o resto: inglês.** Comentários e
descrições de PR, commits, comentários em código, documentos de ticket,
mensagens de Slack, qualquer coisa que outra pessoa vá ler.

**Why:** ele levantou isso em 2026-09-16, depois que eu postei comentários de
review em português nos PRs #49 e #50 do lrgi-terraform. Esses comentários saem
**no nome dele** e ficam no registro do PR — a equipe é distribuída (Ucrânia,
França, Portugal, Grécia) e o idioma comum é inglês.

**How to apply:** vale inclusive para textos curtos e descartáveis, como o
comentário que dispara um teste de CI. Se eu já tiver postado algo em português,
dá para corrigir sem apagar: `gh api -X PUT repos/<org>/<repo>/pulls/<n>/reviews/<id> -f body=...`
atualiza o corpo de um review já submetido.

Relacionado a [[feedback-audit-documentation-style]], que já dizia como escrever
os documentos, e ao bloco "Who you are writing for" — o público define a língua
também, não só o tom.
