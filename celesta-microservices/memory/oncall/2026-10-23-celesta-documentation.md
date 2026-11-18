---
name: 2026-10-23-celesta-documentation
description: "Synthetic \"Celesta Documentation User Journey Check (Daily)\" (hyt-57n-ddp) falhando porque a home de docs.celesta.io mudou; teste desatualizado, não página quebrada"
metadata:
  node_type: memory
  type: project
  originSessionId: f3d1e824-757e-4256-8e15-8104cf0115bd
  modified: 2026-10-23T06:11:28.565Z
---

**Alerta:** `[Synthetics] Celesta Documentation User Journey Check (Daily)`, P2 no PD (P4 no Opsgenie), prod-1. Teste browser `hyt-57n-ddp`, roda 07:00 e 19:00 Lisboa, dias úteis.

**Balde:** ruído, teste desatualizado.

**Causa:** entre 22/10 07:00 e 19:00 um deploy da doc mudou a home: abre em **API Gateway** (antes Backoffice) e as abas viraram API Gateway, Backoffice, Notification. O passo 1 espera `Backoffice gateway AP` na home; os cliques usam XPath posicional (`li[2]`, `li[3]`), então quebram também com a ordem nova. Página no ar, renderizando.

**Ação:** reportar; Randy Martin (último a editar o teste) atualiza texto e locators.

**Histórico parecido, outra causa:** 2025-03-31 o mesmo monitor caiu por 503 em `index.js` da página de notification, asset vindo do unpkg com `@latest` (`@asyncapi/react-component`). Virou CEL-3121 (fixar versão). Se o passo que falhar for o de notification, olhar o unpkg primeiro.

**Checar depois:** run de 23/10 19:00 ou seguinte verde após o ajuste do teste.
