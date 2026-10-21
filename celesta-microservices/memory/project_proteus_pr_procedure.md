---
name: project-proteus-pr-procedure
description: "Quando uma mudança nossa quebra a automação de QA (celesta-qaa-proteus), nós mesmos abrimos o PR lá, com branch de mesmo nome"
metadata:
  node_type: memory
  type: project
  originSessionId: 9ae3c54a-e4cf-43f8-a2ed-299e2136b861
  modified: 2026-10-06T11:56:00.696Z
---

Procedimento novo (2026-10-06, CLS-1546): se um ticket muda um contrato que o `celesta-qaa-proteus` usa (rota, parâmetro obrigatório, payload), **nós** abrimos o PR no proteus, não só avisamos o QA.

- Branch com o **mesmo nome** da branch do ticket nos serviços.
- O CI do proteus roda sozinho com isso.
- O time de QA revisa e faz o merge, se aprovar.

**Why:** o cliente do proteus é escrito à mão (`src/data-services/<serviço>/services/serviceAPI.ts`). O OpenAPI só alimenta o proxy de contrato, que **valida** as chamadas mas não as corrige. Então atualizar a doc do endpoint não basta: o teste quebra no deploy, só que com o motivo escrito.

**How to apply:** ao enumerar a matriz ou planejar uma mudança de contrato, procurar o endpoint em `celesta-qaa-proteus/src`. Se houver chamador, o PR no proteus entra no plano do ticket, como entrega, não como aviso. Primeiro caso: [[cls1546-max-bet-activity]], PUT/PATCH do max bet do game passando a exigir `_source`/`_sourceId`.
