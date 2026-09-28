---
name: cls1872-cls2980-gateway-endpoint
description: "CLS-1872/CLS-2980 — o time criou um endpoint novo no celesta-gateway mas já existia um antigo: decisão é usar o antigo e alinhar com o front"
metadata: 
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-25T10:12:06.593Z
---

Daily de 2026-09-21: o time informou que criou um **endpoint novo no `celesta-gateway`** para o
fluxo de game connections, mas que **um endpoint antigo equivalente já existia**.

**Decisão: usar o antigo.** O novo não deve ser adotado. Alinhar com o **time de front** antes de
implementar qualquer coisa que dependa disso.

**Why:** duplicar rota no gateway para o mesmo recurso cria dois contratos para o front manter e
duas superfícies de permissão para auditar — exatamente o tipo de dívida que o épico CLS-1872 está
tentando reduzir ao centralizar a gestão de game gateways no Backoffice.

**Identificados em 2026-09-25 (a confirmar com Franco que a daily falava destes).** "celesta-gateway"
é quase certamente o `GatewayBundle` do backoffice (`/api/gateway/…`), não o serviço celesta-gateway:

| | Antigo | Novo |
|---|---|---|
| rota | `game_gateway_list` `GET /api/gateway/domain/{id}/game/gateway_configurations` | `integration_game_provider_list` `GET /api/gateway/domain/{id}/integration/game-providers` |
| origem | pré-existente, `Game/GameGatewayController`, tag `Game gateway` | CLS-1458-CLS-1855, 2026-09-11 (`fdb738ad84`), tag `Integrations` |
| permissão | `PS_GAME_GATEWAY_CONFIGURATIONS_LIST` | `PS_INTEGRATIONS_READ` ∨ SEE ∨ EDIT (CLS-2980) |
| shape | id/name/type, paginado + filter + order | card de integração: status, datas, options |
| chama no game | `/api/game-gateways` (filtro) | `/api/domain/{id}/game-gateways` |
| consumidor no front | `services/workers/bonusModel.js:29` (wizard de bônus) | `services/workers/integrations.js:4` (página Integrations) |

O épico CLS-1872 construiu POST/PUT sobre o **novo**. Se a daily mandou usar o antigo, o épico foi
na direção oposta — decisão do Franco. Impactos de unificar no antigo: modelo de permissão diferente
(bônus, não integrações → `options` vazaria para quem tem bônus sem filtro), shape diferente que o
wizard de bônus depende, e cada um chama um endpoint diferente do game.

**How to apply:** não assumir unificação; levantar com Franco qual endpoint a daily nomeou. Se for
o antigo, é redesenho dos PRs do backoffice; se for o serviço celesta-gateway de verdade, esta nota
não se aplica ao épico.

Contexto técnico completo do ticket em [[cls1872-cls2980-findings]].
