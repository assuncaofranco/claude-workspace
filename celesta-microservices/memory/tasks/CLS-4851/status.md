---
name: cls4851-gamblehub-blank-options
description: "Expedite CLS-4851/CLS-4852 — Gamble Hub com game_api_url/user_id vazios não sincronizava; correção na leitura (factory), PR game #1460; falta pp1 e comentário ao Francisco"
metadata:
  node_type: memory
  type: project
  originSessionId: 61467fff-13bc-4cf9-bf46-0c205bdb264e
  modified: 2026-11-11T10:08:51.825Z
---

Expedite aberto pelo Francisco em 2026-11-11 depois da brand do domínio 53 (prod-1) não conseguir
sincronizar jogos de uma conexão Gamble Hub criada pelo form novo do CLS-2979.

Causa: o form do BO manda `""` em todo opcional; o game grava como vem; a
`GameGatewayClientFactory` só caía no fallback com chave ausente. Correção (PR celesta-game #1460,
sub-task CLS-4852): vazio/espaços/null em `game_api_url` e `user_id` vira não preenchido na factory.
Dados e resposta da API não mudam. Revisão sdd limpa em 2 rodadas.

Estado em 2026-11-11: PR pronto, CI pedido ao time. pp1 verde (branch no ar, domínio 56): conexão
nova `80` "CLS-4851 - test config" criada pelo BO com os dois campos `""` (gravados assim), sync
importou 2992 jogos; a `79` do Francisco também (2992); lançamento do jogo 151772 (ativei jogo e
estúdio 2609, ambos da conexão 80) deu 200 com iframe do Gamble Hub. Spans do Gamble Hub não ficam
retidos em pp1, então o user_id enviado não é observável lá. Falta: comentário do Lucas ao Francisco
no CLS-4851 e o merge. Config 137 de prod já corrigida à mão em 2026-11-10.

**Why:** o desenho mudou três vezes (gravação × leitura, todos os tipos × só Gamble Hub). O que
fechou: só Gamble Hub não testa a lista de jogos antes de salvar, e os dois campos têm um leitor só.

**How to apply:** detalhes e casos de pp1 em `tickets/CLS-4851/matrix.md`; instruções de deploy em
`tickets/CLS-4851/deployment-instructions.md`. Melhoria futura (options tipadas, normalização na
gravação) fica para o ticket de validação, não para este.
