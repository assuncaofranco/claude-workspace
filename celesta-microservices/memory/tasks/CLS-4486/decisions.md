---
name: cls4486-decisions
description: "CLS-4486 (game, pai CLS-3063) game_user_id — sem backfill dos users antigos, fallback `??` por provider; o que cada provider recebe hoje"
metadata:
  node_type: memory
  type: project
  originSessionId: f26eb871-d6d0-4f52-8685-538c1f44acd2
  modified: 2026-11-05T10:40:54.007Z
---

Pai CLS-3063 (spec + split por Marcello, 2026-11-02); sub-task CLS-4486 é do Lucas, celesta-game.

**Decisão (Lucas, 2026-11-03): sem backfill.** Users antigos ficam com `game_user_id` NULL; lançamento e
callback caem no id de hoje **por provider** (`$user->getGameUserId() ?? <valor de hoje daquele provider>`).

**Why:** a linha de `game.user` é por jogador × moeda × país do IP, não por provider — a mesma linha serve
CGA e Evolution. O backfill do pai ("populate to playerId or userId depending on the integration", linha
aninhada no Scope IN) teria que gravar um valor só por linha: `user_id` quebra Evolution & cia, `id` quebra
CGA. E `user_id` repetido entre linhas do mesmo jogador violaria o unique. OUT do pai e a sub-task já dizem
"no backfill"; a linha aninhada é sobra.

**How to apply:** registrar no Decisions do plano com a pergunta, a decisão, o motivo acima, e citar a linha
do pai que não é seguida, senão o sdd-reviewer acusa divergência com a spec.

O que cada provider recebe hoje (lançamento), conferido 2026-11-03:
- `user_id` (conta, repete entre moedas): CGA (`QuantaProvider.php:125`), Play'n GO (`AuthenticateHandler.php:52`), GambleHub (`GambleHubProvider.php:87`) — é o defeito
- `id` (linha): Evolution, Pragmatic, SoftGamings, Betsoft, Wazdan, AleaPlay, Redgenn, Yggdrasil
- `id` com zero à esquerda até 4 dígitos: GitSlotPark (`GitSlotParkProvider.php:74-77`)
- Relax, Bongo: `id` (Relax `VerifyTokenHandler:56`, Bongo `LoginHandler:54`)
- Fica `user_id` mesmo com id novo: `testaccount` da CGA, chamadas à wallet e a grants, logs

**Decisão D5 (Lucas, 2026-11-03): Betsoft, GitSlotPark e Yggdrasil buscam pelo `game_user_id` quando o id
recebido casa com `^PID[0-9]+GUID[0-9]+$` (busca pela coluna, não parse da string); senão, como hoje.**
**~~No PHP o callback resolve pelo token~~ — REVISTO no mesmo dia, estava errado.** Betsoft (todo callback
menos authenticate, `BetsoftProvider:212-213`), GitSlotPark (todo callback, `GitSlotParkBundle
AbstractHandler:46-50`) e Yggdrasil (sem token, `BaseGameSessionAbstract:36-40`; erro `:273`) acham a
sessão pelo id do jogador, com repositório tipado `int` — `PID…GUID…` quebra. Betsoft e GitSlotPark estão
em uso. O item "resolve from game_user_id" da sub-task vale para o PHP. Os outros 11: token, ou id de
sessão do provider (GambleHub, Redgenn).
**Lição:** a afirmação "os 14 acham pelo token" veio de olhar só o `GameSessionManager` e a CGA; a
estratégia de busca mora em `*Provider::getGameSessionFromRepository`, um por provider — conferir os 14.

**Decisão (Lucas, 2026-11-03): free rounds entram no 4486.** A concessão acontece dentro do lançamento
(`GameLaunchManager:95`) e leva o id do jogador em 11 providers; a sub-task só diz "launch and callbacks".
Mesmo `getProviderPlayerId(...)` na concessão e no cancelamento, senão o provider dá as rodadas a um id que
nunca entra. Nenhuma outra sub-task cobre. Vai para o Decisions do plano.

**Decisão (Lucas, 2026-11-03): código nos 14 bundles, teste nos 8 em uso.** Em uso (PO, 2026-09-29):
CGA, GitSlotPark, GambleHub, SoftGamings, Evolution, Redgenn, Betsoft, Relax. Yggdrasil chega pela CGA.
Os 6 fora só ganham unitário; o bug antigo do cancelamento da Yggdrasil (conta × linha) fica fora.
Vai para o Decisions, para o revisor não ler "não testado" como lacuna.

**Decisão (Lucas, 2026-11-03): deploy em duas etapas, migration primeiro.** PR só com a migration,
mergeado e deployado antes do código (merge = deploy automático). "Tolerate the column not existing" não
é implementado no PHP: coluna mapeada no Doctrine quebra toda leitura se faltar, e a migration roda no
initContainer do pod (`celesta-argocd .../game/kustomize/base/game.yaml:313-321`). Compendium §2.2 é do
Notion, não nosso: vai nas instruções de deploy com o formato novo.
Por que duas etapas é necessário, não só prudente: os 3 workers SQS e os 10 cronjobs do game usam a
mesma imagem sem esperar a migration. Infra mudando: em 2026-11-03 (CEL-9673, Atit) preprod-1..4 e
staging-1 passaram a migrar num Job PreSync do Argo (antes de qualquer recurso); prod-1 ainda usa o
initContainer só no Rollout da API. Reconferir o prod-1 antes de escrever as instruções de deploy —
a cópia local do celesta-argocd estava velha, sempre `git fetch` e ler `origin/master`.

CLS-4487 (game-go) já em review: PR game-go#118 (Bohdan), regex `^PID[0-9]+GUID[0-9]+$`, coluna
inexistente = vazia. O gerador do PHP tem que casar com isso. Matriz em
`claude-workspace/celesta-microservices/tickets/CLS-4486/matrix.md`.

**Plano escrito 2026-11-03:** PR celesta-game#1447, branch `CLS-4486`, commit `ce4c3a29c`, label
`sdd-plan`. Próximo: `/sdd-implement CLS-4486` (tarefa 1 = branch `CLS-4486-migration`, PR só da
migration). Decisões extras do plano: formato como `private const` no `User` (padrão do repo: constante
técnica interna fica na classe; `celesta-constants` é domínio compartilhado); Proteus semeia `gameUserId`
pelo data service com a chave desligada; sem Postman novo, PP1 manual; Bongo OpenAPI `id` integer→string.
Pendente: doc de regras de id dos providers (Francisco) antes de ligar a chave em prod.
Desvio do fluxo (Lucas, 2026-11-03): a nossa coleção vem **depois** do código, antes do PP1 — local não
alcança provider; callbacks já cobertos por Proteus + PHPUnit. Implement roda em outra sessão; esta revisa.

**Implementação 2026-11-03:** PR da migration celesta-game#1449 (branch `CLS-4486-migration`, já no
GitHub). Código e emenda do plano (`f5830df55`) pushados no #1447, 1574 testes verdes, sdd-reviewer No findings
na rodada 2, labels `sdd-plan` + `sdd-implement`. Proteus PR celesta-qaa-proteus#741 (sem _specs/_plans,
como #720/#618); não compila local (framework 1.4.0 instalado × 1.5.0 pinado, falta `read:packages`), o CI
do PR é o passo 3. Próximo: CI do #741, depois instruções de deploy. Emenda já no plano: `getProviderPlayerId(int|string): int|string` (manter tipo do legado no fio, Lucas);
`env(default:…)` = variável ausente é desligado, Team O deixa de bloquear o deploy; Bongo `id` e AleaPlay
path `{userId}` integer|string no OAS; `CancelWager` resposta (faltou na tarefa 22); Betsoft `<USERID>%d`→`%s`;
wiring em `services_test.yaml` e `AppBundle/Resources/config/services.yml`; teste de payload por provider em
unit test (o mock de curl não grava request). Lição: `make test` com cache velho deu 370 erros falsos
(`BigWinner::$transactionId`, metadata do Doctrine) — limpar `var/cache/test` e pools antes de confiar.

**2026-11-04:** CI do #1447 todo verde (codestyle dos 2 arquivos da AleaPlay corrigido). Proteus#741 **não**
tem CI em PR (`ci.yml` só push no master/dispatch): roda quando o QA mergear, que precisa ser depois do #1447.
prod-1 também passou ao Job PreSync (argocd `bfaf8a0d0c1`, CEL-9673): todos os ambientes migram antes de
qualquer pod. DI: **nos campos do pai CLS-3063** (Lucas, 2026-11-04: nunca na sub-task; campos do 4486
esvaziados), junto com os passos dos irmãos (game-go, BRH); cópia e porquê em
`tickets/CLS-4486/deployment-instructions.md`. Post-deployment dos PRs #1447/#1449 virou só o link para o CLS-3063
(2026-11-04). Comentário 91686 editado com o aviso das linhas FR/BR/JP do 282570. Ficou sem corrigir, por
decisão do Lucas ("mínimo"): a seção de deploy da descrição do pai (ainda pede `false`) e o primeiro bullet
da sub-task; a decisão está no plano. Rollback = desligar a chave se ela já foi ligada; reverter só
se nunca foi.

**PP1 2026-11-04, chave desligada:** branch no ar (coluna + índice, migration 09:13 pelo PreSync). Player
282570 (`lucastest`, domínio 56) lançou com IP alemão 85.214.132.117 → linha nova 13438 EUR/DE NULL, todos os
lançamentos seguintes reaproveitaram. 200 em CGA, SoftGamings, GambleHub, Play'n GO, Relax. GitSlotPark 400:
sandbox `ggapi.loginxgamesapi.com` dá NXDOMAIN (ambiente, não código). Evolution/Betsoft/Redgenn sem lançamento
em pp1 há 30 dias. game-go em pp1 roda a branch CLS-4384 de outra pessoa. A chave em pp1 é uma linha no
ConfigMap `celesta-argocd-parameters/preprod-1/game/parameters.yaml`. Driver: `scratchpad/pp1_launch.py <gameId> <ip>`.

**PP1 2026-11-04, chave ligada 10:22–10:29 UTC** só no pod da API, por `public/.user.ini` com
`auto_prepend_file` (o `index.php` tem `disable_dotenv`, o conf do fpm é do root e o Argo tem selfHeal, então
`kubectl set env`/ConfigMap volta sozinho). Casos 1, 3, 4, 5 verdes; linhas 13439 FR, 13440 BR, 13441 JP com
id. Lucas: game-go fora dos nossos testes. Comentário 91686 no CLS-4486 para o Francisco (testar com o
CLS-4487; aposta e ganho com id novo ficam com ele). #1447 aprovado, #1449 sem aprovação.

**2026-11-05, review do Socrates no #1447:** schema OpenAPI da resposta da Yggdrasil corrigido para
integer|string (`375f5d346`); cancel de free round legado da Yggdrasil respondido como fora do escopo
(plano, Out of Scope), aguardando ele. Ticket de volta para To review. O Francisco questionou env var × Flipper
no Slack: a escolha veio da spec do Marcello (TL é dono da spec no SDD novo), não foi discutida conosco.

Switch = env var `GAME_USER_ID_GENERATION_ENABLED` do Team O, não Flipper (game já sem Flipper, [[CLS-3150]]).
País do game user é o do IP no lançamento (`PlayerNormalizer`), não o do cadastro.
