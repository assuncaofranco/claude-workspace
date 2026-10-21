---
name: our-services
description: "Quais microserviços são do nosso time (D-Team) — game, promotion, cms, cms-v2, contact; a wallet sai quando terminar a remoção do bônus"
metadata:
  node_type: memory
  type: project
  originSessionId: 7c16fbf2-1a26-475a-8ca1-a2bb9c56e895
  modified: 2026-10-20T13:07:20.300Z
---

Nossos MS, segundo o Lucas (2026-10-20): **celesta-game, celesta-promotion, celesta-cms, celesta-cms-v2 e celesta-contact**.
Componente Jira do time: `D-Team`.

A **celesta-wallet** ainda é parcialmente nossa só por causa do bônus legado. Ela deixa de ser nossa quando
terminar a remoção do bônus da wallet (épico CLS-1277, limpeza CLS-1283). Ver [[wallet-ownership-shift]].

**Backoffice e gateway não são nossos, mas são a porta de entrada de todos os serviços.** Quando uma
implementação nossa depende deles, mexemos neles no que diz respeito ao nosso ticket. A administração
deles (manutenção geral, dívida técnica alheia ao ticket, decisões de arquitetura) não é nossa.

**Why:** isso não estava registrado em lugar nenhum (nem no `context.yaml`, nem na memória; a página Team components do Notion não foi consultada),
e define o que significa "nossos MS" quando o Lucas pede uma varredura ou uma limpeza "sem rastro".

**How to apply:** varredura ou limpeza "nos nossos serviços" = esses quatro, mais a wallet enquanto o
CLS-1283 não fecha. BO e gateway entram quando o nosso ticket passa por eles, limitados ao que o ticket toca.
