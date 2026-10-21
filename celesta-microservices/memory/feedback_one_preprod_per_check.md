---
name: one-preprod-per-check
description: Cada verificação roda em um preprod só; não repetir em PP1 o que já passou em PP2
metadata:
  node_type: memory
  type: feedback
  originSessionId: 021a75bb-af4b-402b-b068-e4110dfaefc3
  modified: 2026-10-14T07:55:43.080Z
---

Não há obrigação de testar em dobro. O que passou num preprod está coberto; o outro preprod só entra para
o que o primeiro não consegue testar (ex.: CLS-505, PP2 sem jogo Relax → só os webhooks Relax e free
rounds no PP1).

**Why:** dito pelo Lucas em 2026-10-14 no QA do CLS-505, ao ver uma tabela que marcava PP1 como
"pendente" para itens já verdes no PP2. Preprod é compartilhado e disputado; repetir gasta janela.

**How to apply:** ao planejar ou reportar cobertura, a coluna é "onde foi testado", não "local × PP1 ×
PP2". Pendente só é o que nenhum ambiente cobriu ainda. Ver [[cls505-qa]].
