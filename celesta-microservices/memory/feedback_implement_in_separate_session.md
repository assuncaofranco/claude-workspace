---
name: feedback-implement-in-separate-session
description: Lucas roda o sdd-implement numa sessão nova e mantém a sessão do planejamento aberta para revisar o que o processo produziu — em vez de /clear
metadata:
  node_type: memory
  type: feedback
  originSessionId: f26eb871-d6d0-4f52-8685-538c1f44acd2
  modified: 2026-11-03T14:11:51.993Z
---

Em ticket grande, o Lucas **não** faz `/clear` antes do `sdd-implement`: abre outra sessão para a
implementação e deixa a sessão que fez entendimento, matriz e plano aberta, gerenciando e revisando
o resultado (PR, report do implement, Proteus).

**Why:** "esses contextos que temos aqui nos tem ajudado a rever o que é feito pelo processo" (CLS-4486,
2026-11-03). A sessão nova dá o contexto limpo que o `/clear` daria — o implement não herda alternativas
descartadas — e a sessão antiga guarda o porquê de cada decisão, que é o que pega desvio no review.

**How to apply:** quando a fase de código chegar num ticket grande, não sugerir `/clear`; dizer o comando
para a outra sessão e esperar o report voltar aqui para revisar contra a matriz e as decisões. Refina a
regra de `/clear` do `router.md` (CLS-1283) — se virar padrão, levar ao `rules/corpus.md`.
