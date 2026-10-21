---
name: cls3290-review
description: "Review do upgrade do celesta-contact para Symfony 7.4 (PR #424, autor Rasoul); código ok, só divergência de spec, desfecho = mensagem sem reprovar"
metadata:
  node_type: memory
  type: project
  originSessionId: 440f9323-162e-4512-bae5-0a52c7139067
  modified: 2026-10-12T06:29:08.168Z
---

celesta-contact PR #424, 2026-10-12. Lucas como revisor.

**Código ok:** lock sem `symfony/*` em 8.x nem 6.x fora o `monolog-bridge` 6.4.45 documentado, `conflict`
igual ao backoffice, libs nas versões do plano, CI todo verde.

**Achados (só doc):**
- Commit `21205077` muda o OpenAPI (`discr` fixo + `required` em EDP/SendGrid) para passar no Proteus,
  que está vermelho no master desde 2026-08-31 e virou bloqueante no CEL-9115. Correção certa, mas o
  AC em `_specs/CLS-3290.md:60` diz que o OpenAPI não muda. Spec precisa registrar.
- Spec sem matriz; não bloqueante para upgrade.
- Plano (linha 73) diz que `InputBag::get()` passa a rejeitar não escalar no 7.x; já era assim desde o
  6.0. Sem comentário.

**Desfecho:** mensagem ao Rasoul pedindo os ajustes, ticket **não** volta para Ready. Regra em
`global/rules/review-lens.md`. Ver [[github-approval-vs-real-review]].
