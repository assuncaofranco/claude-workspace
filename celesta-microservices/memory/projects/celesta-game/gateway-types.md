---
name: celesta-game-gateway-types
description: "CGA é o gateway_type_quanta — o agregador da própria Celesta; mapa entre o nome comercial que Produto usa e o tipo técnico, e quais dos 19 tipos o game realmente sabe instanciar"
metadata:
  node_type: memory
  type: project
  originSessionId: ac86a1f1-7cb7-43de-b034-de3b1dcd6c74
  modified: 2026-09-29T14:44:02.654Z
---

**CGA, "Celesta game aggregator", é o `gateway_type_quanta`.** É o agregador da própria Celesta,
não um fornecedor de fora. Dito pelo Franco em 2026-09-29.

**Por que isso não se descobre no código.** Procurei "CGA" e "aggregator" no celesta-game, no
celesta-backoffice, nas constantes e no celesta-game-go: zero ocorrência. A `options` do quanta aponta
para `casino.api.quanta.com`, que parece domínio de terceiro e por isso o descartei na primeira
passada. Produto fala em nome comercial, o código só tem nome técnico, e não existe tabela ligando os
dois. **Quando um nome de gateway não aparece no grep, a resposta é perguntar a Produto, não continuar
procurando.**

**Os 14 tipos que o game instancia** têm um bundle cada em `celesta-game/src/`. O
`GameGatewayClientFactory` faz `switch` no tipo e cai num `throw ProviderException(CLIENT_NOT_IMPLEMENTED)`
no fim. Logo bundle existente = tipo utilizável:

    AleaPlay Betsoft Bongo Evolution GambleHub GitSlotPark PlaynGo
    Pragmatic Quanta Redgenn Relax SoftGamings Wazdan Yggdrasil

**Os 5 restantes de `TYPES` não têm cliente** e estouram na criação: `aleaplay_v2`, `soft_gaming`
(singular, ao lado de `soft_gamings`), `absolute_live_gaming`, `bet_soft` (com underscore, ao lado de
`betsoft`), `reelsoft`. Três deles são variantes de grafia de tipos que existem — cuidado ao escolher
constante pelo nome.

**Lista de suportados do Francisco (PO), 2026-09-29:** CGA/quanta, GitSlotsPark, Gamble Hub,
Softgamings, Evolution, Redgenn, BetSoft, Relax. São 8, todos existentes. Ele quer remover o resto, o
que sairiam 6 com cliente (`aleaplay`, `playn_go`, `bongo`, `pragmatic`, `yggdrasil`, `wazdan`) mais os
5 sem cliente. **Não executado:** `TYPES` mora em `celesta-constants` e é lido por todos os serviços;
remover tipo quebra edição de conexão já gravada com ele, e não dá para conferir produção sem sessão
AWS. Fica como ticket próprio, fora do CLS-1872.

**Onde moram os campos de cada tipo:** `GameGatewayConstants::OPTIONS_BY_TYPE`, criado no
CLS-1872-CLS-2979 (PR celesta-constants#601), no formato do
`ProviderConstants::OPTIONS_BY_PROVIDER` do payment. Ver [[cls1872-review-2026-09-22]].

**Why:** o épico inteiro passou perto de remover tipo errado e de documentar o provedor errado no
exemplo, porque ninguém tinha o mapa nome comercial → tipo técnico.

**How to apply:** ao receber lista de gateways de Produto, traduzir para o tipo técnico **antes** de
tocar em qualquer coisa, e tratar nome não encontrado como pergunta, não como tipo inexistente.
