---
name: oncall-2026-11-11-celesta-mcp
description: "celesta-mcp p50 latency > 200ms em prod-1 — ruído de amostra pequena, 3 chamadas reais de get_player_list (~850 ms) num serviço com ~6 req/h"
metadata:
  node_type: memory
  type: project
  originSessionId: 784020e5-20e1-4f4b-bdff-5fcb14d48197
  modified: 2026-11-11T14:09:08.746Z
---

**Alerta:** `[prod-1] celesta-mcp | HTTP request p50 latency > 200ms in 30m` (monitor 124939520, criado por Randy Martin em 2026-09-29), P3, PD atribuído ao Bohdan. Disparou ~14:00 UTC de 2026-11-11.

**Balde:** ruído, monitor mal calibrado.

**Evidência:**
- Tráfego base de ~6 hits/h (GET/POST `/mcp` de 0 a 5 ms, parece keepalive/healthcheck). Entre 11h e 13h UTC subiu para 20 a 32/h.
- Na janela, 3 chamadas `mcp__backoffice__get_player_list` vindas do `Crisp-HugoMCP` (chatbot de suporte), cada uma chamando `POST /api/gateway/domain/{domainId}/players` no gateway: mediana de 841 ms, máximo de 976 ms. Todas 200.
- As outras tools (get_player_information, get_player_wallet, authorize_user) ficaram entre 35 e 101 ms.
- Com tão poucas requisições em 30 min, 3 chamadas reais de tool já puxam o p50 acima de 200 ms. Às 14h o p50 voltou a 0.

**Saída:** REPORTAR. Sem erro, sem dinheiro, só leitura; resolve sozinho.

**Para depois:** o monitor precisa de volume mínimo (ex.: só avaliar com hits > N em 30 min) ou ser medido no `mcp.tools_call` com threshold realista, porque as tools fazem proxy para o gateway e a busca de players leva naturalmente ~1 s. Dono do monitor: Randy. A lentidão da busca de players no gateway (`POST /players`, ~850 ms) é o sinal real, se alguém quiser olhar.

Houve alarmes do celesta-mcp em `#celesta-alarms-prod-1` em 09-29, 10-07, 10-09, 10-13, 10-26 e 11-05. Não conferi qual monitor era cada um.
