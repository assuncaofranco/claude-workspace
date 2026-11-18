# CLS-4851 — campos opcionais vazios em conexões Gamble Hub

Expedite. Sub-task única: CLS-4852 (celesta-game), PR #1460. Substitui a matriz provisória
`game-options-empty-string`, que descrevia o desenho descartado (limpar na gravação, todos os tipos,
queries de produção).

## Escopo final

O form do BO manda `""` em todo campo opcional, e o game grava como vem. No Gamble Hub, dois campos
quebravam: `game_api_url` (sincronização sem endereço, "URI must include a scheme and host") e
`user_id` (id vazio no lugar do id do login). A correção é na leitura, no único lugar que lê os dois:
`GameGatewayClientFactory`, caso `TYPE_GAMBLE_HUB`. Vazio, só espaços ou null vira não preenchido e
cai no fallback que já existia (`office_api_url`; id do login no construtor do `GambleHubClient`).
Dado gravado e resposta da API não mudam.

## Decisões (Lucas, 2026-11-11)

- Na leitura, não na gravação: os dois campos têm um leitor só, e a correção vale também para o que
  já está gravado.
- Só Gamble Hub: os outros tipos testam a lista de jogos antes de salvar, e para eles `""` não quebra
  nada (leem direto ou com `?? ''`).
- Sem Proteus em expedite, a não ser que a mudança quebre um cenário. Nenhum cenário chama
  `/game-gateways` nem a sincronização do Gamble Hub.
- Prova ponta a ponta em pp1: sincronizar a conexão Gamble Hub de lá, criada pelo Francisco com os
  dois campos vazios. Não limpar os dados de pp1.
- Condição Yoda (`'' === $x`) mantida: é a convenção do repositório.

## Casos para pp1 (células afetadas)

| # | Caso | Esperado |
|---|---|---|
| 1 | conexão Gamble Hub com `game_api_url: ""` e `user_id: ""` (a de pp1) | sincronização termina com `status: true`, jogos listados, sem "URI must include a scheme and host" no Datadog |
| 2 | lançamento de jogo dessa conexão | `openGame` com o id da conta do login, 200 |
| 3 | conexão Gamble Hub sem as chaves (produção, domínios 26/30/33/52/54/55) | igual a hoje, nada muda |

## Contexto que fica do nosso lado

- Produção: config 137 (domínio 53) corrigida à mão em 2026-11-10, chaves removidas. Com a correção,
  continua certa.
- Risco anotado, fora do ticket: se a mesma conta Gamble Hub for usada em dois domínios, um login
  derruba o token do outro ("token superseded by newer login", domínio 52, 2026-11-10 11:11).
- Melhoria futura (ticket de validação): options tipadas por gateway e normalização na gravação.
