---
name: cls4491-review
description: "CLS-4491 review (game #1451, Bohdan, pai CLS-3063) — provider_player_id na lista de rounds do BQ; código ok, plano com linha ofensiva no topo, risco de merge empilhado"
metadata:
  node_type: memory
  type: project
  originSessionId: 48076508-dbb8-44d6-beff-5497cd0bde89
  modified: 2026-11-05T11:44:12.632Z
---

Review 2026-11-05 do celesta-game #1451 (branch `CLS-4491`, base `CLS-4486`, autor Bohdan). Pai CLS-3063, irmão nosso [[cls4486-decisions]].

**Código ok.** Regra do `GameRoundsBigQueryTransformer::resolveProviderPlayerId` conferida contra o CLS-4486:
Quanta/GambleHub/Play'n GO = `user_id` do jogador (`QuantaProvider:125`, `GambleHubProvider:76`, PnG `AuthenticateHandler:52`),
GitSlotPark = `id` com zero até 4, resto = `id`; `game_user_id` vence. Tipo do gateway via `ggc.domain_id`, igual ao etl
(`game_round` filtra por `ggc.domain_id`), e `global.game` já tem `game_gateway_configuration_id`. `GameRound.user` é
NOT NULL, então o inner join novo não some com round. 53 testes verdes no container (o CI do game só roda depois de APPROVED).

**Achados (nenhum de código):**
- `.sdd/_plans/CLS-4491.md:3` tem uma linha xingando a si mesmo/o Claude ("little clown… stupid"), commit `01421c3ee` do
  Bohdan; vai para o master. Decisions também tem "(Claude, from the conversation)" duas vezes.
- PR empilhado em `CLS-4486`: se mergear nele antes do #1447, o select de `gr.user_id`/`gr.game_user_id` vai junto com o
  launch fix e a lista de rounds do BQ responde 400 até o CLS-4644 estar aplicado. Retarget para master depois do #1447 e só
  mergear no passo 7 do deploy do pai (merge = deploy).

Desfecho proposto: mensagem, não volta para Ready. Lucas não comenta no GitHub (não quer marcar); manda as frases por fora.

DI do pai (campo Deployment instructions, 2026-11-05): BRH passo 6 já põe o 4491 depois do etl, mas o BRH vale
"any time after launch fix step 1", e o #1451 carrega o código do 4486 → faltava dizer "depois do passo 2 do launch fix" e
"retarget para master". Sugerido.

Resposta do Bohdan (Slack, 2026-11-05): a frase do plano é intencional → Lucas deixou pra lá. Retarget: o GitHub só
muda a base quando a branch base é **apagada**; `delete_branch_on_merge` é false no game (e na wallet), então só é
automático se alguém apagar `CLS-4486` depois do merge do #1447.

**Correção:** a ordem ESTÁ na DI do próprio CLS-4491 (campo Deployment instructions da sub-task, editado 2026-11-05
11:32): passo 1 "Wait until celesta-game on branch CLS-4486 is deployed". Eu tinha olhado só o pai. Na DI do pai continua
faltando — ver [[feedback_parent_deploy_instructions]].
