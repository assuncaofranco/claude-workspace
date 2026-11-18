---
name: payment-ddtrace-case-collision
description: "celesta-payment sempre mostra tests/Stubs/DdTrace.php modificado no Mac; não é alteração, não fazer stash nem descartar"
metadata:
  node_type: memory
  type: project
  originSessionId: 07575302-3568-4218-8336-7f61606542bd
  modified: 2026-11-12T11:58:45.696Z
---

O celesta-payment versiona `tests/Stubs/DdTrace.php` e `tests/Stubs/ddtrace.php`. O disco do Mac não distingue
maiúscula, então o checkout grava os dois no mesmo arquivo e o `git status` sempre mostra `M tests/Stubs/DdTrace.php`.

**Why:** dito pelo Lucas em 2026-11-12 (plano do CLS-4933), quando o sdd-plan parou por "working tree sujo".

**How to apply:** não tratar como alteração do usuário: nunca stash nem checkout/descartar. Pode criar branch e
commitar normalmente, adicionando só os arquivos pelo nome, nunca `git add -A`. O hook de pre-commit roda o
phpinsights nele e aprova.
