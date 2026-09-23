---
name: never-fix-outside-ticket-scope
description: "Nunca consertar código fora do escopo do ticket, por melhor que a correção pareça — em casino o prejuízo de quebrar algo em produção é milionário"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-09-21T10:36:30.355Z
---

Achar um defeito fora do escopo do ticket **não** autoriza corrigi-lo. Nem depois de investigar, nem
quando a correção parece obviamente certa, nem quando ela é pequena. Reportar e seguir.

Isso vale para o escopo no sentido amplo: a descrição do ticket, e também a spec e o plano que nós
mesmos escrevemos — cujo objetivo é entregar o ticket, não consertar o que vimos de errado no caminho.

**Why:** a Celesta é casino, e quase todo código toca dinheiro. Um comportamento "errado" em produção
com frequência está errado por causa de dados antigos que ninguém vai auditar a tempo, e o código
tolerante é o que mantém tudo de pé. Endurecer esse código transforma um dado sujo e inofensivo em
indisponibilidade. O caso que originou a regra (CLS-1872, 2026-09-21): eu propus fazer o
`GameGatewayClientFactory` do celesta-game lançar exceção quando falta chave em `options`, em vez de
deixar virar `null` silenciosamente. Tecnicamente melhor. Mas a factory está no caminho do
`launchGame()` — jogador abrindo jogo — e qualquer config antiga sem uma chave adicionada depois
pararia de abrir jogo. Prejuízo milionário para resolver um problema que não era do ticket. A própria
investigação prévia não justificava o risco.

**How to apply:** ao encontrar algo assim, escrever no documento do ticket e levar ao TL/PO como
observação. Se a decisão for consertar, é ticket próprio, com o escopo e o risco declarados nele.
Enquanto isso, implementar o ticket contra o comportamento **atual** do sistema, mesmo que o atual
seja frágil — e, quando o teste revelar essa fragilidade, registrar o resultado como informação, não
como defeito a corrigir ali.

Relacionado: [[feedback_ask_before_workaround_on_stack_problems]] (problema de stack vai para o Lucas,
não vira contorno) — mesma família: não resolver sozinho o que não é meu.
