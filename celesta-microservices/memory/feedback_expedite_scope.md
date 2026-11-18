---
name: expedite-scope
description: "Expedite é urgência de produção, não feature: a resposta que o consumidor vê não muda, e o ticket corrige só o que causa o problema"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d34c3823-e8f6-442c-ae5f-e331f1339aa3
  modified: 2026-10-30T09:12:12.050Z
---

Num ticket do tipo Expedite, nada pode mudar na resposta que o consumidor (BO, front, gateway) recebe. A
correção fica restrita ao que causa o problema em produção. Melhoria de contrato ou de produto vai para outro
ticket, mesmo que seja barata.

**Why:** dito pelo Lucas no CLS-4314 (2026-10-30), quando perguntei se o relatório deveria passar a mostrar o
`potentialWinnings`: *"nada pode mudar para a resposta do BO. O conceito de expedite é uma urgência em prod, não
feature."* Antes disso ele já tinha recusado criar e adaptar endpoints às pressas em produção, até ver que a
mudança era aditiva.

**How to apply:** na matriz de um expedite, toda célula que mudaria a resposta é N por princípio, e entra um
critério transversal: para a mesma entrada, a resposta da branch é idêntica à do master. Preferir mudança
aditiva (rota nova, rota antiga intacta) e deploy em ordem segura.
