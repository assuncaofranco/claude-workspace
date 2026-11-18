---
name: cls3860-understand
description: "CLS-3860 (bundles CA + TP, pai CLS-3597) — pcov = sem branch (leitura do time 2026-11-10); CA já ok; TP sem testes e não roda fora do game"
metadata:
  node_type: memory
  type: project
  originSessionId: 61f33b57-0789-47e1-b3b6-1612821b14e6
  modified: 2026-11-16T12:08:24.072Z
---

Assumido por Lucas em 2026-11-10, movido para Planned. Pai CLS-3597 (branch coverage), avô CLS-3204.

**Leitura do time (2026-11-10):** onde o driver é pcov, não há modo branch; 100% por linha basta.
Rasoul fechou CLS-3853 (game) e CLS-3854 (promotion) sem PR com o comentário "we are using PCOV there
and it doesn't support branch check"; Socrates fechou game-go e notification no mesmo dia, sem PR; contact
#439 (CLS-3855) só sobe o gate 70→100. Bate com o CLS-3204 ("if you use pcov, dont use xdebug").
Lucas aceitou: pcov + 100% = ok; abaixo disso, trabalhar; xdebug = medir branch.

- **custom-attributes-bundle:** PHPUnit + CI pcov gate 100 desde CLS-3894 (#48 master, #49 development). Nada a fazer.
- **test-provider-bundle:** sem tests/, phpunit.xml, workflow; composer.json sem require de nada além de php/ext.
  ~4k linhas em src. Não carrega fora de um app host: 71 `use App\AppBundle`, 13 `App\ApiBundle`, estende
  `ProviderFactory` e `WebhookManager` do game. Game o tem em `require-dev` ^1.6, bundles.php só dev/test.
  `src/Promotion/` estende classes de **celesta-promotion** (`AddBonusOfferSubscriber`,
  `FreeRoundConfigurationType`), mas promotion master não requer o bundle — a esclarecer.

**Não é testado pelo game:** nenhum teste do game referencia `Celesta\TestProviderBundle` (os hits de
"TestProvider" são homônimos), e o coverage do game só conta `src/`. O CA roda sozinho porque o src dele tem 0
imports `App\` e o host entra por `AssetInterface` (fake `tests/Fixtures/Entity/TestAsset`).

**Tamanho de stubs:** 50 classes `App\` distintas (37 game, 12 promotion, 1 nos dois); 9 herdadas/implementadas;
ProviderFactory 14 deps, WebhookManager 17. Recomendação: não escrever stubs à mão; no CI, checkout do
celesta-game (e da promotion se `src/Promotion/` estiver viva) e autoload-dev `App\` → src deles.
Precedente do mecanismo: gateway ci.yml:145 baixa celesta-auth master com `CELESTA_GITHUB_TOKEN_PULL_REPOS`
(org secret, visível no repo do TP). Uso novo: ninguém carrega código PHP de outro serviço em unit test.

**Decisão 2026-11-10 (Lucas, com aval do Marcello, autor):** apagar `src/Promotion/` (a7e31ad, free round para a
promotion; nenhuma branch da promotion instala o bundle). Junto saem `Resources/config/services_promotion.yml` e o
registro condicional do mapping Doctrine em `TestProviderBundle.php:15-26` e o load condicional em
`TestProviderExtension.php:16-24`. Consequência: o CI só baixa o game.

**Matriz assinada 2026-11-10** (`claude-workspace/celesta-microservices/tickets/CLS-3860/matrix.md`): A = boot no
game depois da remoção + gate de CI (100% passa, <100% falha). Campo Github repository preenchido com
`celesta-test-provider-bundle`. Spec do pai fala em branch: no sdd-plan, passar a decisão pcov como Decision.

**Entrega (Lucas, 2026-11-10), substitui a ideia de CI próprio no bundle:** split em dois MS. Bundle: limpeza
(Promotion + guard `class_exists(Game)`). Game: `composer` aponta `dev-CLS-3860` do bundle e os testes rodam lá,
com o `src/` do bundle na cobertura do game (gate 100). As duas branches andam juntas até testado e aprovado; só
então o Marcello faz o merge do bundle, cria-se a tag (v1.7, manual, sem workflow de release; game trava v1.6
hoje) e corrigimos o composer do game para a tag. Testes moram no game (`tests/TestProviderBundle/`), não no
bundle (Lucas, 2026-11-10): é o único lugar que os roda, e evita mapear namespace de teste para `vendor/`.
Matriz revista no mesmo dia (dimensão "evento de CI" caiu; gate é o do game). Guard `class_exists(Game)` também
sai (Lucas: se outro serviço instalar no futuro, adapta-se o bundle). Decisões com fundamento, no formato do
template do sdd-plan, em `claude-workspace/celesta-microservices/tickets/CLS-3860/decisions.md`.

**Sub-task do game criada 2026-11-10: CLS-4837** (`celesta-game`, Lucas, bloqueada por CLS-3860). CLS-3860 = só a
limpeza do bundle. Matriz revista assinada. Próximo: `/sdd-plan CLS-3860`, depois `/sdd-plan CLS-4837`.

**Jira corrigido 2026-11-10 (com aval do Lucas):** CLS-3860 renomeado para "Remove the unused promotion support from
test-provider-bundle", descrição = só a limpeza. Pai CLS-3597 renomeado para "{D} Reach 100% CC with pcov line
coverage", parágrafo novo explicando pcov × branch (texto original era do Marcello/Janis).

**Plano escrito 2026-11-11:** PR #10 no test-provider-bundle (branch `CLS-3860`, só `.sdd/_plans/CLS-3860.md`),
label `sdd-plan`, custo $5.71 comentado. Review Fable+Opus antes: o game resolve o bundle pelo Private Packagist (branch
só instalável depois do sync); getBalance manual roda em `dev` (a stack local é `APP_ENV=dev`, o banco de test é vazio);
"silent 404" trocado por "services silently skipped" (sintoma não verificado); Decision branch×line foi só para o plano
do CLS-4837. Próximo: `/sdd-implement CLS-3860`, depois `/sdd-plan CLS-4837`.

**Implement 2026-11-11:** `7daca93` no PR #10 (inverso exato do a7e31ad), game com a branch verde (2164 testes),
review 1 rodada sem achados (`sdd-reviewed`), Proteus pulado, manifesto `celesta-releases/releases/CLS-3597.yaml`
(g1 bundle #10, g2 manual tag v1.7 + repin do game), DI/rollback no pai junto com o contact #439, custo $10.46
($16.17 no ticket). Armadilhas do game local: `CLS-4852` pede PHP 8.5 e o container é 8.4 (`--ignore-platform-req=php`),
game sem nginx (getBalance via kernel), banco local sem gateway test-provider.

**Novo em 2026-11-11:** Virgile criou CLS-4874 (promotion) e CLS-4875 (contact) "Switch coverage to Xdebug and gate
100% branch coverage" (suítes <30 s no CI). Contradiz o parágrafo que pusemos no pai ("branch só onde já é xdebug").
Pendente com o Lucas antes do `sdd-plan CLS-4837`.

**Virada 2026-11-11 (Virgile, no Slack: "None of the two, generate tests with AI"):** os testes do bundle ficam
**no próprio bundle**, com stubs das classes do game, não no game. O game não muda nada (`^1.6` pega a 1.7).
O CLS-3860 fechou só como limpeza: plano emendado (`a1e72c6`), PR #10 com post deployment "merge #10, depois o PR do
CLS-4837, depois tag v1.7", manifesto sem o repin, DI do pai e descrição do 3860 atualizadas. O CLS-4837 vai ser
re-apontado para `celesta-test-provider-bundle` (branch a partir de `CLS-3860`, PR contra master; cuidado com a
armadilha de PR empilhado), molde = CI e `TestAsset` do custom-attributes-bundle. Ideia de pcov no vendor
(whitelist `~^/var/www/app/(?!src/|vendor/celesta/test-provider-bundle/src/)~`, medida ok) ficou descartada.
Matriz casos 5 e 6 precisam virar o gate do CI do bundle.

**Fechamento 2026-11-11 (fim do dia):** CLS-4837 **cancelado** pelo Lucas (só existia por causa do game). Tudo no
CLS-3860, que virou "…and cover it at 100%" (título do Jira e do PR #10). Plano emendado `f7ec8cc`: tasks 1–5 feitas
(`7daca93`), 6–17 = `require-dev` (phpunit ^11.5, symfony framework-bundle/form/console/validator/serializer/yaml
7.4.*, doctrine/orm ^2.20), `autoload-dev` `App\` → `stubs/App/` (fora de `tests/` por causa do aviso psr-4), stubs
copiados do game `328257a3d`, só unitário, CI cópia do custom-attributes em PHP 8.4, sem reflection/ignore. Comando
local = `docker run` da imagem `celesta/game:latest-dev` com `-d pcov.directory=/app/src` (testado). PR #10, manifesto
e DI do pai sem CLS-4837 (merge #10 → tag v1.7). Custo no Jira $17.98. Próximo: `/sdd-implement CLS-3860` numa
conversa nova (testes, ~30 arquivos).

**Entregue 2026-11-11 (noite), CLS-3860 em To review:** PR #10 com `ebf0dd8` no topo. Suíte própria do bundle: 234
testes, 100% linhas (1145/1145), CI cópia do custom-attributes; stubs em `stubs/App/` (39 + getters), plano emendado 3x
(pacotes do game em require-dev + `repositories` do Private Packagist; ProviderFactory/WebhookManager só assinatura;
fallback morto do ratio no `GameSynchronizer` removido). Review: rodada 1 = 2 should-fix (tests) + 1 nit (dead-code),
rodada 2 limpa, `sdd-reviewed`. Game real com a branch: compila, 4 rotas, getBalance igual, 2164 verdes; revertido.
Custo no Jira $48.11. **Pendentes:** 30 threads do bot `datadog-official` ("Exception should be thrown") abertos no PR —
falso positivo em `expectExceptionObject(new …)`, decisão do Lucas; dois defeitos antigos para ticket (BET_DENIED com
mensagem duplicada; validação aninhada dos forms não roda). Depois do aceite: Marcello merge #10 → tag v1.7.

**Fechamento final 2026-11-11 (noite), To review:** depois de 2 revisores sem contexto, rodada de endurecimento
(task 19, mutação: 8 sobreviventes mortos), 247 testes / 100%, review SDD rodadas 3–4 limpas, game master `328257a3d`
com `4df7b2a`: igual à baseline (2164). Head `cbef8ae`. Jira do 3860 descreve tudo (inclui fallback e pacotes do game).
Limites registrados: CI nunca rodou (só dispara com approve), argumentos do `services.yml` só pela verificação no game,
`export-ignore` follow-up. Follow-up a abrir: BET_DENIED msg duplicada, validação aninhada, `totalBalance` morto,
`=== 'ONLINE'` sempre true. Próximo: Lucas pede approve → 1º CI; review humano; Marcello merge + tag v1.7.

**2026-11-16, Implemented:** Socrates aprovou o PR #10 → 1º CI rodou e passou (247 testes, gate 100% verde, head
`4d56de9`). Ele comentou no `ci.yml:13` que `cancel-in-progress: true` + job pulado (verde) deixa mergear sem o gate;
respondemos que é o mesmo bloco do custom-attributes e do game (padrão do time) e que as duas correções sugeridas não
fecham o buraco (review posterior ainda deixa check `tests` pulado no head) — proposta: ticket para o padrão de CI
compartilhado. Lucas vai falar com ele. Falta: merge do Marcello + tag v1.7; follow-ups (export-ignore, 4 defeitos antigos).

**Pendente (antigo, já resolvido acima):** onde os testes do TP rodam (stubs no bundle × dentro do game × outro); sub-task tem 2 repos e o
sdd-plan exige um.
