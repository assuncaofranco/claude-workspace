---
name: promotion-proteus-ci-master
description: "master da promotion nunca roda o Proteus (verified tree gate), então \"master verde\" não prova contrato; e o 404 documentado como `message` quando a API devolve `title`"
metadata:
  node_type: memory
  type: project
  originSessionId: 72444775-1c68-4835-bc7c-9c8a2375edcd
  modified: 2026-11-06T11:59:54.261Z
---

No CI da promotion, o push no master pula `proteus / isolated-tests`: o "Verified tree gate" acha o marcador deixado pelo PR. Master verde não diz nada sobre Proteus; um bug de contrato só aparece no próximo PR que roda a suite.

Suite ligada ou não vem do Qase (`initTestCase` → `toExecute`). Ligar uma suite (QAA-1138, 2026-11-05 ligou a pcpr-34 de reasons) expõe bug que já estava no master e quebra todo PR seguinte de uma vez.

Caso de 2026-11-06: `NotFoundSchema` em `src/Kernel.php` documentava `message`, a API devolve `title`. Falhava o OpenAPI de todo 404 checado. Correção `d14a12944` no CLS-2962-CLS-4067 (#570), cherry-pick no CLS-4034 (#586) como `6d586274e`. CLS-3293 tinha a mesma falha.

**Why:** gastei tempo culpando o bump do proteus-framework 1.6.1 (era só refactor) antes de comparar com o PR que passava.
**How to apply:** Proteus vermelho em vários PRs ao mesmo tempo → primeiro diffar o PR verde mais recente contra o master, depois a suite no Qase, só por último o framework. O framework é legível: `read:packages` está no token do `gh`, `npm pack` com `.npmrc` temporário.
