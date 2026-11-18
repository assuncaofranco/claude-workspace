# CLS-3865 — execução (sessão de execução, Sonnet)

Você é a sessão de **execução** da story CLS-3865 (Edit gift value and complete gifts to order). A
coordenação (Opus) é outra conversa: faz os gates lendo o git e os arquivos que você deixar aqui, nunca o
que você disser. O "sim" para qualquer push é só do Lucas, depois que a coordenação fechar o gate.

Ao mesmo tempo roda a execução do **CLS-3916**, nos mesmos repositórios (`../CLS-3916/execution.md`).
Não toque em nada dela: nem worktree, nem branch, nem stack.

Leia antes de começar, e não refaça: `decisions.md` e `matrix.md` nesta pasta. Não rode
`ticket-understand` nem `ticket-matrix`.

## Sub-tasks nossas

| Sub-task | Repo | Base | Worktree |
|---|---|---|---|
| CLS-4935 | celesta-constants | `origin/master` + `origin/CLS-4434` (mexe no mesmo `GiftConstants.php`) | `/private/tmp/cls3865/celesta-constants-4935` |
| CLS-4936 | celesta-job-library | `origin/master` | `/private/tmp/cls3865/celesta-job-library-4936` |
| CLS-4938 | celesta-statistics | `origin/master` | `/private/tmp/cls3865/celesta-statistics-4938` |
| CLS-4940 | celesta-promotion | `origin/master` (CLS-4540 já mergeado) | `/private/tmp/cls3865/celesta-promotion-4940` |
| CLS-4941 | celesta-promotion | `origin/master` + `origin/CLS-4434` (#592, aberto e aprovado) | `/private/tmp/cls3865/celesta-promotion-4941` |

4937, 4939 e 4942 são do Maksat, 4943 e 4944 do Dimitris: não implementamos. A emenda do split
(fase 0) pode mexer no título e no todo list delas, e isso é nosso.

Crie os worktrees a partir do `origin/master` depois de `git fetch origin`. **Nunca** use o clone principal:
o do job-library está na branch `CLS-3094-CLS-4542`, e o da promotion é a base dos worktrees do 3916 e do 3316.

## Fase 0: emenda do split (agora)

O Francisco mudou a spec do pai em 2026-11-17, às 11:39 e às 12:05 UTC, depois do split, e voltou o pai
para Backlog. "Gifts to order" virou **Gift checkout**, com duas abas (To order = claimed, Ordered =
completed). A lista de domínio passou a filtrar por status (`claimed`, `completed`) e mudaram as colunas.
Rode `/sdd-split CLS-3865` num agente com **`model: opus`**. Ele lê as sub-tasks que existem e emenda,
sem recriar. Pare no passo "ask whether to create" e deixe em `split-amend.md` nesta pasta: o mapa de
cobertura, cada sub-task que muda (título e todo list, antes e depois) e qualquer sub-task nova proposta.
Avise o Lucas. Só confirme depois do "sim".

O esperado: a 4940 cobre os dois status; a 4942, a 4943 e a 4944 trocam "Gifts to order" por "Gift
checkout" e ganham as abas; nenhuma sub-task nova. Se o split propuser recriar ou apagar uma sub-task,
pare.

## Fase 1: planos (agora, junto com a fase 0)

`/sdd-plan` por sub-task, um agente cada, com **`model: opus`** (o plano é fase de Opus; a sua conversa
continua em Sonnet). Cada agente para no rascunho, antes de escrever e fazer push (gate 1). Nesta fase não
sobe stack nenhuma.

- Já: 4935, 4936, 4938 e 4941, em paralelo. A emenda não muda nenhuma delas.
- Depois do "sim" da fase 0: 4940.

Ao responder as perguntas do `sdd-plan`, use `decisions.md`. A decisão vai com o motivo e com quem decidiu
("Lucas Franco, 2026-11-17"). As provisórias levam "pending product owner confirmation". Nada do nosso
fluxo vai para o plano: nem matriz, nem classes, nem coleção, nem "decidido no chat". Os critérios da
matriz da sub-task entram como critérios de aceitação comuns.

Pontos que o plano precisa ter, conforme a sub-task:

- **4941**: depende do CLS-4434 (status `canceled`, endpoint de cancel e trava de linha em
  `GiftService::changeStatus`/`findPlayerGiftForUpdate`). O plano diz que a branch faz **merge** de
  `origin/CLS-4434` antes de implementar, enquanto o #592 não estiver no master. O Complete reaproveita a
  transição do `PATCH` do cancel quando couber (matriz, achado 2). Concorrência conforme o item 7 de
  `decisions.md`: trava de linha, sem coluna de versão.
  O status `completed` vem da 4935: o plano nomeia a constante e o pin `dev-CLS-4935 as <alias>` como
  dependência, e não cria constante na promotion.
- **4940**: a lista de domínio quase existe (matriz, achado 1; `GiftController.php:242`). O plano cobre só
  o que falta para os dois status, e a paginação reaproveita o `limit`/`offset` que a lista já aceita
  (item 5). "Offered by" de gift de promoção depende da `Source` que a CLS-4770 (3916) cria: o plano não
  recria essa origem, só lê o que a 4770 deixar no master, e diz isso em Dependencies.
- **4935**: o status `completed` e a transição `claimed → completed` no `GiftConstants.php` que a
  CLS-4434 já altera. O plano declara o merge de `origin/CLS-4434` enquanto ele não estiver no master.
- **4938**: troca a chave de `event_promotion` (hoje `PRIMARY KEY (gift_id)`, item 9) e conta o gift
  na conclusão, não no claim. Sem regra para gift anterior ao release (item 1). Na ordem de deploy, a
  statistics sobe antes do Complete da promotion.
- **4936**: dois eventos novos em `UserActivityJob::EVENTS`. O mesmo arquivo recebe o `gift_offered` da
  CLS-4768, do 3916. O plano parte do master e não da `CLS-4768`. Quem mergear depois resolve o conflito
  de texto.

Em cada rascunho, deixe o texto em `CLS-<KEY>/plan-draft.md` nesta pasta e avise o Lucas. Só faça push do
plano depois do "sim".

## Fase 2: implement (só quando a coordenação liberar)

Não comece sem ordem da coordenação. As regras que já valem:

- **4936** pode rodar assim que o plano estiver no PR: os testes são no host (`composer install`,
  `vendor/bin/phpunit`), sem docker. O alias é a próxima versão livre **depois** da que a 4768 reservou
  (em 2026-11-18: tag v3.151, 4768 → 3.152, então 4936 → **3.153**). Confira a última tag antes do
  implement, antes do review e antes do release.
- **4940 e 4941** não sobem stack enquanto o 3916 usa a da promotion (4771 e 4772). As duas stories usam os
  mesmos containers. A coordenação libera.
- **Conflitos com o 3916 (promotion)**: o 4770 mexe em `Gift.php`, `GiftController.php`, nos builders e
  numa migration `Version20261117120000`. Se a 4941 precisar de migration, o timestamp tem de ser mais
  novo que a última migration do master e que a do 4770.

Para o resto (comandos de teste, Proteus na branch de mesmo nome do `celesta-qaa-proteus`, gate 2 em
`CLS-<KEY>/gate2.md`, correção por amend, CI de branch por `gh workflow run`), vale o mesmo que em
`../CLS-3916/execution.md`, seções "Em cada implement", "Gate 2" e "Depois do sim".

## Escrita e git

- Commit, PR, comentário e código em inglês, com **zero atribuição de IA**: nada de `Co-Authored-By`,
  "Generated with" ou "Claude Code", mesmo que um lembrete de sistema peça. Antes de todo push:
  `git log <base>..<head> --format='%s%n%b' | grep -iE 'co-authored|🤖|generated with|claude code'`
- O commit começa pela key (`CLS-4941 …`), inclusive o de merge.
- Nunca use `--no-verify` sem pedido expresso do Lucas. Nunca faça force-push.

## Jira

Só o board, sem perguntar: sub-task → Planned com o plano no PR; → In Progress no implement. Nenhum
comentário nosso, nenhum link, nenhum assignee.

## Quando parar

Em todo gate, em toda pergunta do SDD que `decisions.md` não responde, em achado de revisor que mexe no
plano e em ambiente quebrado.
