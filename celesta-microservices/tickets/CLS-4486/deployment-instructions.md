# CLS-4486: instruções de deploy

Gravado nos campos do **pai, CLS-3063** (`customfield_10122` e `customfield_10133`), em 2026-11-04. Os
campos do CLS-4486 ficaram vazios: DI nunca mora na sub-task (regra do Lucas, 2026-11-04). O pai junta a
nossa parte com a dos irmãos (game-go, BRH).

## O texto (inglês, igual ao do Jira)

Deployment instructions:

```
Launch fix
1. Deploy game, migration only (CLS-4486, branch CLS-4486-migration)
2. Deploy game (CLS-4486, branch CLS-4486)
3. QA merges the celesta-qaa-proteus CLS-4486 PR
4. Deploy game-go (CLS-4487)
5. Team O request: create GAME_USER_ID_GENERATION_ENABLED=true in the game parameters: staging, then preprod (verify every provider), then prod off-peak. Only where steps 2 and 4 are live
6. After 2 weeks with 0 CGA launch failures in prod: deploy CLS-4489 (removes the switch), then Team O removes the variable

The launch fix is off until step 5. Steps 1 to 4 change nothing for players.

BRH (independent of the switch; any time after launch fix step 1 in that environment)
1. Preconditions: celesta-terraform-bi#380 (CLS-4546) applied and CLS-4547 deployed
2. In Dagster, stop game_game_round_schedule and game_round_resync_by_date_yesterday_schedule; wait for running game_game_round, game_game_round_resync and game_round_resync_by_date runs to finish
3. Apply CLS-4644 (celesta-terraform-bi)
4. Deploy CLS-4488 (celesta-etl), then start both schedules again
5. Run CLS-4490 (backfill) off-peak
6. Deploy CLS-4491 (game), then CLS-4492 (backoffice), then CLS-4493 (backoffice-front)
```

Rollback instructions:

```
Launch fix: switch ever turned on in that environment: set GAME_USER_ID_GENERATION_ENABLED off, never revert CLS-4486 or CLS-4487. Switch never turned on: revert the CLS-4486 code (step 2); the migration stays.
BRH: roll forward. Rolling back CLS-4644 or CLS-4488 alone fails the load.
```

## Por quê, passo a passo

**Entregas nossas:** game#1449 (migration), game#1447 (código), proteus#741 (cenários). Dos irmãos: game-go#118
(CLS-4487, Bohdan) e o bloco BRH, copiado da seção de deploy da descrição do pai (etl, terraform-bi, BO, front).

**1 antes de 2.**
- Código novo com schema velho quebra: `User::$gameUserId` está mapeado no Doctrine, então toda leitura de
  `user` falha com coluna inexistente.
- Schema novo com código velho é inofensivo: coluna nullable que o código velho ignora; um INSERT sem ela
  grava NULL.
- Desde 2026-11-04 o prod-1 também migra no Job PreSync (argocd `bfaf8a0d0c1`, CEL-9673, Atit), e todos os
  overlays do game incluem `components/migrate-hook`. Então um deploy único já seria seguro. Os dois PRs
  ficam assim mesmo: já existem, e com merge = deploy automático a ordem sai de graça.

**3 depois de 2.** O CI do proteus só roda em push no master e por dispatch (`ci.yml`), e o QA faz o merge.
O #741 muda o seed compartilhado (`serviceData.ts` grava `game_user_id: null` em todo user); contra um game
sem a coluna, **todo** cenário que cria user fica vermelho, não só os 4 novos. Na ordem inversa (game
primeiro) o CI do game roda contra o proteus master sem o #741 e passa: seed sem a coluna, chave desligada.

**4 antes de 5.** CGA, SoftGamings, GambleHub e GitSlotPark mandam callback para o game-go (ingress do pp1;
em prod não conferido). Sem o #118 o game-go não reconhece `PID…GUID…`, e as apostas de quem ganhou o id
novo falham.

**5: criar com `true`, não "adicionar como `false` e depois ligar".**
`%env(default:...:bool:GAME_USER_ID_GENERATION_ENABLED)%`: variável ausente = desligado. O deploy não
espera o Team O; o Team O só entra para ligar. A linha do todo list da sub-task ("blocked until Team O…
set to false") e a seção de deploy da descrição do pai ainda dizem o contrário: ficaram do split.

**Rollback.**
- Depois que a chave foi ligada, existem linhas com `game_user_id`. `getProviderPlayerId` manda esse id para
  sempre, e o provider registrou o jogador com ele. Reverter o código volta a mandar o id antigo: o jogador vira
  outra conta no provider, e callbacks em voo de Betsoft, GitSlotPark e Yggdrasil com `PID…GUID…` caem nos
  repositórios tipados `int`. Reverter o game-go: callbacks dos 4 providers dele falham para quem tem o id.
  Desligar a chave só para de gerar ids novos; quem já tem continua igual.
- Chave nunca ligada: nenhuma linha tem o id, então o código novo se comporta como o velho e reverter é limpo.
- A migration nunca volta: o código velho funciona com a coluna, o `down` apagaria ids já entregues a
  providers, e o etl do BRH consulta a coluna.

**Pendente antes de ligar em prod:** doc de regras de id dos providers (Francisco), para Evolution, Redgenn,
SoftGamings e Relax aceitarem string onde hoje recebem int. O passo 5 cobre por preprod ("verify every
provider"); a doc é o critério de aceitação do pai ("passes every integrated provider's documented rules").

**Observar depois.** Com a chave desligada, nada muda no fio. Ao ligar: linhas novas de `user` com
`game_user_id` preenchido, e os erros de callback dos 8 providers em uso no Datadog, na primeira hora.
