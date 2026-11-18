# Memory Index

Regra de **como trabalhar** não está aqui — está em `../../global/rules/`, carregada pelo
`../../global/router.md`. Este índice é só o que aconteceu.


Root = global only. Ticket status in `tasks/<ticket>/`, per-service knowledge in `projects/<name>/`, incidents in `oncall/<AAAA-MM-DD>-<serviço>.md` — read on demand. (payment: DdTrace.php sempre "modificado" no Mac, não é alteração.)

Ticket workflow is skills (`~/.claude/commands/`), not memory; `oncall` is separate; routing in `~/.claude/CLAUDE.md`.

- [Repositório claude-workspace](../../global/memory/claude-workspace-repo.md) — skills/memória versionados desde 2026-09-23; credencial só em `~/.claude-secrets/`
- [CLS-1285-CLS-2391 fix](tasks/project_cls1285_cls2391_status_set_at_fix.md) — implicit Doctrine listener-ordering bug pattern (celesta-wallet), and the correct `dev-{branch}` composer pattern for an unreleased job-library change
- [CLS-1285-CLS-2391 review decisions](tasks/project_cls1285_cls2391_review_decisions.md) — pending: apply Copilot's null-guard on 3 promotion handlers; composer dev-branch stays until PO approves
- [Sensor/ANJ reporting flow](project_sensor_anj_reporting_flow.md) — root cause: wallet `Metadata` requires `countryOfBirth` and throws before the sensor call (preprod player 282557)
- [CLS-2450-CLS-2452 duplicate sub_balance](tasks/project_cls2450_cls2452_duplicate_subbalance_investigation.md) — two races (cron×URL in RewardHandler, URL×URL TOCTOU in PlayerPromotionLimitValidator); wallet has no idempotency
- [Oncall incidents](oncall/) — one file per alert triaged via `/oncall` (08-29 SQS spike no segment; 09-01 healthcheck 089, modelo `bonus.id == sub_balance.id`)
- [CLS-1843-CLS-1912 currency-nullable](tasks/project_cls1843_cls1912_currency_nullable.md) — promotion, implementação verde; criação preguiçosa da wallet; falta review/commit + tag do celesta-fixtures
- [CEL-8373 change-password confirmation email](tasks/project_cel8373_change_password_confirmation_email.md) — root cause: celesta-auth Go `change_password.go` never dispatches the `TransactionalEmailJob`; systemic
- [CLS-2387 duas branches no cms](tasks/project_cls2387_cms_two_branches.md) — `CLS-2387` vs `CLS-2387-custom-attrbiutes`; arg `LoggerInterface` auto-mergeado sem marcador
- [CLS-1186 master merge](tasks/project_cls1186_master_merge.md) — merge 2026-09-15 herdou a query do master e matou a feature (corrigido 09-16); lição das "duas metades com conjuntos de eventos opostos"
- [Testar preprod-1 com Newman](tasks/project_cls1186_preprod_newman.md) — token do BO em `oauth/2.0/token`; domínio 213 = Sportsbook; colisão `bet.potentialWinnings`
- [Ler o banco de preprod e staging](reference_preprod_db_read.md) — `dbal:run-sql` no pod via kubectl; nunca prod; staging-1 é outra conta, namespace `celesta`
- [Spec ownership shift](project_spec_ownership_shift.md) — devs own spec + ticket-specific tests, PO only does final cross-ticket integration; no downstream net, which is *why* `ticket-matrix` is mandatory and Claude enumerates while Lucas classifies
- [CLS-1872 (game connections) planejamento](/Users/l.franco/Desktop/celesta-projects/claude-workspace/celesta-microservices/tickets/CLS-1872/epic.md) — ordem 2980 → 2978 → 2979 → 2981, decisões D1/D2
- [CLS-1872 especificidades para testar](tasks/CLS-1872-CLS-2980/testing-specifics.md) — só `aleaplay` não pinga; chaves dos 14 tipos; perfis de permissão em preprod
- [CLS-1872-CLS-2980 endpoint do gateway](tasks/CLS-1872-CLS-2980/gateway-endpoint.md) — daily 2026-09-21: existe um endpoint novo e um antigo no celesta-gateway; **usar o antigo** e alinhar com o front; quais são exatamente ainda não foi verificado em código
- [Armadilha do merge de PRs empilhados](project_stacked_pr_merge_trap.md) — pilha mergeada de uma vez fica na base, não no master; conferir com `git diff --stat origin/master..origin/<branch>`
- [APPROVED no GitHub ≠ review](project_github_approval_vs_real_review.md) — aprovação antiga é carimbo; CI de branch só por Run workflow (`[run-ci]` revertido); review começa quando o ticket vai para Review
- [Dois Lucas](user_two_lucases.md) — o usuário é Lucas **Franco**; Lucas **Azevedo** é o TL de DevOps (novo, set/2026), autor dos commits do celesta-argocd — não atribuir commits de infra ao usuário pelo primeiro nome
- [Captura de body no nginx do game](project_game_nginx_body_capture.md) — game e promotion logam body com `cashiertoken` em claro (prod, 2026-09-22); bloqueia o deploy do CLS-2978/2979
- [CLS-2594-CLS-3055 review do gift](tasks/CLS-2594-CLS-3055/review.md) — o que é um gift, onde mora o KPI de generosity (`master_player_report`, celesta-statistics) e os três buracos do épico fora do PR
- [Árvore de permissões do backoffice](projects/celesta-backoffice/permission-tree.md) — policy ≠ permission; fixtures do vendor desatualizadas, nunca concluir "o pai não existe" por elas
- [CLS-2594-CLS-3107 review do gateway de gift](tasks/CLS-2594-CLS-3107/review.md) — backoffice #3194 (Socrates) + fixtures #290; 7 comentários postados 2026-09-24; contém dois erros meus para não repetir
- [CLS-412-CLS-2923 decisões e contrato](tasks/CLS-412-CLS-2923/decisions.md) — promotion, offer sem BO user, idempotente; PR #535; por que a chave é do caller, decisão H (`source_scenario_id`)
- [CLS-1872 review 2026-09-22](tasks/CLS-1872/review-2026-09-22.md) — reviews dos 6 PRs e o que foi feito depois; pendente decisão do Lucas: force-push para tirar trailer de atribuição de 7 commits
- [Tipos de gateway do game](projects/celesta-game/gateway-types.md) — **CGA = `gateway_type_quanta`**; Produto fala nome comercial, código só o técnico
- [CLS-3223-CLS-3224 review da expiração](tasks/CLS-3223-CLS-3224/review.md) — promotion PR #536: o bônus claimed agora só expira depois que a wallet confirma (lock sem espera deixava o sub_balance vivo); pendente: bônus sem sub_balance fica claimed para sempre
- [CLS-2847-CLS-2848 matriz de QA](tasks/CLS-2847-CLS-2848/matrix.md) — flag `move_bonus_to_promotion` (BO #3201, gateway #1486); pós-merge `FlipperClient` morto quebra `WorkerStateIsolationTest`
- [CLS-2851 flag cleanup no game](tasks/CLS-2851/scope.md) — game #1417; em pp1/pp2/pp4/prod-2 o game nunca leu a flag, então o PR troca o cancel de wallet para promotion
- [CLS-1546 activity do max bet](tasks/CLS-1546/decisions.md) — game centraliza `max_bet_limit_updated` com `_source`; BO para de despachar; lembretes pendentes no arquivo
- [PR no proteus é nosso](project_proteus_pr_procedure.md) — mudança de contrato que quebra a automação de QA: nós abrimos o PR no `celesta-qaa-proteus`, mesma branch do ticket, CI roda sozinho, QA faz o merge; o OpenAPI só valida, não corrige o cliente
- [Hotfix ids inteiros no reward configuration](tasks/hotfix-reward-configuration-int-ids.md) — promotion #546; como assinar chamada local à promotion (HMAC)
- [CLS-419-CLS-3392 emissor de gift](tasks/CLS-419-CLS-3392/decisions.md) — promotion despacha `GiftEventJob` no POST de gift; replay fora do escopo
- [Wallet saindo do nosso escopo](project_wallet_ownership_shift.md) — wallet vai para o time A; CLS-3376 cortado e voltou (2026-10); CLS-3371 saiu de vez
- [CLS-3471-CLS-3486 errors da wallet no game-go](tasks/CLS-3471-CLS-3486/decisions.md) — branch nasce de CLS-595 (não master); o PHP grava `[code, msg do HTTP client]`, não os erros da wallet; pendente sign-off da matriz + 2 perguntas da spec
- [CLS-3290 review do Symfony 7.4 no contact](tasks/CLS-3290/review.md) — PR #424 (Rasoul): código ok, só o spec diverge do commit que conserta o Proteus; desfecho = mensagem, sem voltar para Ready
- [Piloto dos cards de mudança](project_change_cards_pilot.md) — combinado 2026-10-12: no próximo ticket, cascata de perguntas por fronteira (HTTP, entidade, job); Lucas responde, eu confiro com o código; objetivo é ele reter o domínio
- [CLS-505 QA do Symfony 7.4](tasks/CLS-505/qa.md) — game/contact/cms verdes no local 2026-10-13, coleções prontas para pp1; promotion #548 bloqueado no Proteus; nunca publicar T&C em pp1; armadilhas do local (global-container, 8 GB, gateway PHP 8.5)
- [CLS-2485 escopo do cleanup de jobs](tasks/CLS-2485/scope.md) — MoveBonusCleanup: o que sai (jobs de status, 3 commands no-op, `bonus:cancel`, CronJobs do prod-2) e o que fica (`adjust-bonus-balance` é sub_balance, não legado); assumimos o que era do CLS-1624
- [CLS-3734 expedite do schedule não iniciado](tasks/CLS-3734/decisions.md) — promotion #554; contar do fim da ocorrência anterior; v1.375 verificada em prod-1 2026-10-16
- [CLS-3376 review da wallet no claim](tasks/CLS-3376/review.md) — wallet #1897/#1898 + proteus #643 (Bohdan); #1898 quebra o cancel da promotion master, só entra depois da promotion #545; mockAPI do proteus ainda manda `status: canceled`
- [CLS-850 review do old_ rename](tasks/CLS-850/review.md) — wallet #1912/#1913 + proteus #668 (Bohdan); cap de migrated bonus via promotion pode dar 404 eterno; migration sem lock timeout; conflita com o nosso #1911
- [CLS-3877 sign T&C 503](tasks/CLS-3877/triage.md) — falha no crm (404 do cms vira 500/503 em domínio ANJ); cms ok, pendente decisão de barrar publish sem todos os idiomas
- [Nossos microserviços](project_our_services.md) — game, promotion, cms, cms-v2, contact (D-Team); a wallet sai quando fechar o CLS-1283; BO/gateway não são nossos, mas são a porta de entrada: mexemos neles só no que o nosso ticket toca
- [CLS-3150 tirar o Flipper dos nossos MS](tasks/CLS-3150/scope.md) — Lucas+Marcello 2026-10-20: Flipper sai de wallet/BO/gateway; sub-tasks 3150, 3904, 3905, 3906
- [CLS-3543 medição de cobertura do notification](tasks/CLS-3543/measurement.md) — Go; precisa `GITHUB_ACCESS_TOKEN=$(gh auth token) make init`; CI hoje sem gate e sem total; baseline 25.4% / 43.8% / 52.6% conforme o que conta
- [CLS-3542 review da cobertura do contact](tasks/CLS-3542/review.md) — PR #428 (Bohdan): 100% local, mas o retry 5xx do EDP é código morto em prod (Guzzle lança antes) e o PR cobre com Response fake; gate segue 70
- [CLS-3894 review do PHPUnit no custom-attributes](tasks/CLS-3894/review.md) — PR #48 (Rasoul) limpo, CI 100%; falta a parte B em development para fechar o AC
- [CLS-3897 tooling fora do épico de cobertura](tasks/CLS-3897/decision.md) — test-utilities, clock-mock e fixtures excluídos do CLS-2947 (comentário postado 2026-10-26); falta um admin do org arquivar o clock-mock
- [Proteus no master da promotion](projects/celesta-promotion/proteus-ci-master.md) — master pula o Proteus (verified tree gate); 404 documentado `message` vs `title` real quebrou todo PR depois do QAA-1138; corrigido em `d14a12944`
- [Locks da promotion são cluster-wide](projects/celesta-promotion/locks.md) — `local_redis` engana: é Valkey externo por ambiente (argocd-parameters), então lock por transação e por configuration serializam entre pods
- [CLS-3676 idempotência do money-path](tasks/CLS-3676/decisions.md) — promotion; pai = depósito duplicado + 409 (opção B, só claimed); chave de idempotência é transação × configuration, não × promotion; spec ainda por rodar
- [Deploy de branch em preprod](reference_preprod_branch_deploy.md) — Jenkins sobe a branch antes do merge; exige último review `APPROVED`, todo push descarta
- [Depósito de teste em preprod](reference_preprod_deposit.md) — gateway `POST /payment` com token do player; cartão no vault; gerador Newman em `postman/CLS-3676/gen_pp1_deposit.py`; sem `bonusIds` para testar deposit_tier
- [CLS-4067 review da guarda de moeda](tasks/CLS-4067/review.md) — promotion #570 + wallet #1927; 2 bloqueantes; ler Goal+Scope+AC juntos antes de rebaixar achado
- [CLS-4163 motivos de gift na promotion](tasks/CLS-4163/decisions.md) — `reasonId`/`reasonName`; gifts existentes apagados; BO antes da promotion; plano PR #581
- [CLS-4314 N+1 do transaction report](tasks/CLS-4314/decisions.md) — expedite; rota bulk por domínio na promotion + BO por chunk; id de depósito é único global (payment auto-increment); rota atual fica (gateway e sportsbetting usam)
- [CLS-4337-CLS-4338 QA do free round em outra moeda](tasks/CLS-4337-CLS-4338/qa.md) — wallet #1946; local verde, pp1 montado no 282570 (bônus 1166005 USD), Francisco joga; valor não é convertido, pergunta ao PO
- [CLS-3507 numerical custom attributes](tasks/CLS-3507/review.md) — assumidos de outro time em 2026-11-02: crm #2117 (3793) e BO #3283 (3796); bloqueio real é o bundle CLS-3791 (sem PR, assignee Lucas); desvios de SDD listados
- [Expedite não é feature](feedback_expedite_scope.md) — resposta do consumidor não muda; matriz ganha critério "branch == master" para a mesma entrada
- [Projeto em inglês, nossos arquivos em pt](feedback_team_artifacts_english.md) — repo, Jira, git, PR sempre em inglês; memória e tickets/ podem ser pt
- [DI vai no pai](feedback_parent_deploy_instructions.md) — Marcello lê só o pai; juntar a nossa com a dos outros devs
- [Sem Reviewer no Jira](feedback_no_jira_reviewer.md) — D-Team não usa o campo; To review sem preencher
- [Login do Celly Dev](reference_celly_dev_login.md) — usuário lfranco; esqueceu a senha → só a pergunta-lembrete
- [App pessoal Lucas+Claude](project_personal_app.md) — Celly Dev (`celly-dev/`), cópia podada do e2e rodando no host; board com Jira real desde 2026-11-09, Requests feito; próximo é o chat
- [CLS-4195 review da moeda no depósito](tasks/CLS-4195/review.md) — gateway #1545 (Bohdan): código ok; só o plano em `_plans/` em vez de `.sdd/_plans/`; mover os mocks tem lógica
- [Um preprod por verificação](feedback_one_preprod_per_check.md) — não repetir em PP1 o que passou em PP2; o segundo preprod só cobre o que o primeiro não consegue
- [CLS-4486 game_user_id sem backfill](tasks/CLS-4486/decisions.md) — game, pai CLS-3063; linha do game user serve todos os providers, então backfill é impossível; fallback `??` por provider; quem recebe `user_id` hoje (CGA, PnG, GambleHub)
- [CLS-3540 QA do refactor de cobertura do cms](tasks/CLS-3540/qa.md) — cms #281 (Rasoul); pp1 verde depois do deploy em 2026-11-03 (só o 403 de permissão na lista de T&C do BO); chave `content-block` no GW, filtro de segmento do player dentro de `filter`
- [CLS-4491 review do provider_player_id](tasks/CLS-4491/review.md) — game #1451 (Bohdan): código ok, 53 testes verdes; plano com linha ofensiva no topo; empilhado em CLS-4486, não mergear antes do CLS-4644
- [CLS-4540 gift requests na promotion](tasks/CLS-4540/decisions.md) — matriz fechada 2026-11-06; plano PR #591; implement só depois do merge do #586
- [celesta-fixtures: merge é release, ids disputados](projects/celesta-fixtures/merge-and-ids.md) — push no master gera tag; PRs abertos disputam os ids numerados; o backoffice carrega as fixtures em test
- [CLS-3680 review da doc do document-created](tasks/CLS-3680/review.md) — notification #173: schema bate com crm #2147 e o Go; só nits
- [Implement em outra sessão](feedback_implement_in_separate_session.md) — ticket grande: sem `/clear`; implement numa sessão nova, a do plano fica aberta para revisar
- [CLS-4851 Gamble Hub com opcionais vazios](tasks/CLS-4851/status.md) — expedite; correção na leitura (factory), game #1460 revisado; falta pp1 (conexão do Francisco, não limpar) e comentário ao Francisco
- [CLS-3860 testes dos bundles CA e TP](tasks/CLS-3860/understand.md) — pcov = sem branch (leitura do time 2026-11-10); CA já ok; test-provider sem testes e só carrega dentro do game
- [Piloto global write + tickets do Team A](project_global_write_pilot.md) — write em 64 repos; 3 tickets do A no 15-Beedrill (4779, 1214, 418), formato só SDD; fazemos todas as sub-tasks, inclusive B, e o time dono aprova o merge
- [CLS-3916 prontidão do gift em promoção](tasks/CLS-3916/readiness.md) — split sem rota de activity na promotion; 3316 e 3865 abertos; perguntas ao PO e ao Marcello (entidade Source)
- [CLS-3865 coordenação](/Users/l.franco/Desktop/celesta-projects/claude-workspace/celesta-microservices/tickets/CLS-3865/execution.md) — eu coordeno (Opus), execução em Sonnet; nossas 4936/4940/4941; colide com o 3916 na stack da promotion e no `UserActivityJob`
- [Juiz de permissões](project_permission_judge.md) — hook + juiz de modelo ligado nos chats normais em 2026-11-18; o que nunca vai ao juiz, como auditar, e por que apagar o allow do settings gasta mais token

**Pending triage (not yet sorted into the structure above):**
- [Infra repos structure](reference_infra_repos.md) — repo list ok, AWS-account claims wrong (see infra memory `project_infra_context.md`)
- [PC migration gotchas](reference_pc_migration_gotchas.md) — transitional (deadline 2026-08-18 passed); likely archivable
