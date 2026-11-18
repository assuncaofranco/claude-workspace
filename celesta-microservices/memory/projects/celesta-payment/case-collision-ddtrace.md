---
name: payment-ddtrace-case-collision
description: "celesta-payment versiona tests/Stubs/DdTrace.php e tests/Stubs/ddtrace.php; no macOS o clone sempre aparece com DdTrace.php modificado, e não é alteração de ninguém"
metadata:
  node_type: memory
  type: project
  originSessionId: 62088cdd-c327-4fdb-8c35-d9d5e7834bae
  modified: 2026-11-12T11:56:26.094Z
---

Desde CLS-3511 (2026-10-22, commit ffa5e8951) o celesta-payment tem dois arquivos que só diferem na
maiúscula: `tests/Stubs/DdTrace.php` (classe `Tests\Stubs\DdTrace`) e `tests/Stubs/ddtrace.php`
(função `DDTrace\root_span`). O disco do Mac não distingue maiúscula, então qualquer checkout grava os
dois no mesmo arquivo e o `git status` mostra `DdTrace.php` modificado. Visto em 2026-11-12, depois do
fast-forward do master (15-Beedrill, CLS-4933).

**How to apply:** não tratar como alteração local nem fazer stash ou descarte (volta sozinho). Para
commit, adicionar arquivos pelo nome, nunca `git add -A`. Teste que use `Tests\Stubs\DdTrace` pode
falhar localmente no Mac sem ser regressão; o CI (Linux) tem os dois.
