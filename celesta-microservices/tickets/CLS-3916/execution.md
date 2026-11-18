# CLS-3916 — execução (para a sessão de execução, Sonnet)

Você é a sessão de **execução** da story CLS-3916 (Offer gifts from promotions). A coordenação (Opus) é outra
conversa: faz o gate 2 lendo o git e os arquivos que você deixar aqui, nunca o que você disser. O "sim" para
qualquer push é só do Lucas, depois que a coordenação fechar o gate.

Leia antes de começar, e não refaça: `decisions.md` e `matrix.md` nesta pasta, e o plano de cada sub-task em
`.sdd/_plans/<KEY>.md` na branch dela. Todos os planos passaram no gate 1. Não há pergunta aberta.

## Sub-tasks

| Sub-task | Repo | PR do plano | Worktree |
|---|---|---|---|
| CLS-4767 | celesta-constants | #635 | `/private/tmp/cls3916/celesta-constants` |
| CLS-4768 | celesta-job-library | #561 | `/private/tmp/cls3916/celesta-job-library` |
| CLS-4769 | celesta-activity | #525 | `/private/tmp/cls3916/celesta-activity` |
| CLS-4770 | celesta-promotion | #604 | `/private/tmp/cls3916/celesta-promotion-4770` |
| CLS-4771 | celesta-promotion | #605 | `/private/tmp/cls3916/celesta-promotion-4771` |
| CLS-4772 | celesta-promotion | #606 | `/private/tmp/cls3916/celesta-promotion-4772` |
| CLS-4774 | celesta-backoffice | #3343 | `/private/tmp/cls3916/celesta-backoffice-4774` |
| CLS-4775 | celesta-backoffice | #3344 | `/private/tmp/cls3916/celesta-backoffice-4775` |

Fora: CLS-4773 (cancelado), CLS-4776 (front, do Dimitris). Se um worktree sumiu, recrie de `origin/<KEY>`.

## Levas

`/sdd-implement` por sub-task, num agente cada, até o pedido de push (gate 2). Uma stack por repositório de
cada vez: duas sub-tasks do mesmo repositório nunca rodam juntas.

1. **Leva 1:** 4767, 4768, 4769 e 4770, em paralelo (quatro repositórios).
2. **Leva 2,** depois do push de 4767: 4771 (pin `dev-CLS-4767 as <alias>`) e 4774 (idem).
3. **Leva 3,** depois do push de 4768, 4770 e 4771: 4772 e 4775.
   - 4772: antes de implementar, **mergeia** `origin/CLS-4743`, `origin/CLS-4770` e `origin/CLS-4771` na
     `CLS-4772` (merge, nunca cópia de código nem rebase; mensagem `CLS-4772 Merge <branch> into CLS-4772`).
     Pin `dev-CLS-4768 as <alias>`.
   - 4775: pin `dev-CLS-4768 as <alias>`.

Pin: o alias é a próxima versão que ainda não existe. Confira `git tag --sort=-v:refname | head -1` da
biblioteca antes do implement, antes do review e antes do release (em 2026-11-18 o constants já está em v1.369 (CLS-5181, de outro time): o alias do 4767 é **1.370**; em 2026-11-17: constants v1.368 → 1.369;
job-library v3.151 → **3.152**; os planos de 4772 e 4775 dizem 3.150, que já existe: use a próxima livre).

## Em cada implement

- `git fetch origin`; código lido do `origin/master`.
- Teste: o comando da Testing Strategy do plano. constants `make test`; job-library no host
  (`composer install`, `vendor/bin/phpunit`); activity, promotion e backoffice `make init` e depois os alvos
  do plano. Ambiente quebrado (credencial, container, rede): pare e conte. Não contorne.
- Proteus (4769, 4770, 4771, 4772): na branch de mesmo nome do `celesta-qaa-proteus`, como o plano diz.
  O clone tem `.env`. Não rodamos Proteus local; o CI do serviço valida.
- O código segue o plano e nada além. Achado de revisor que pede mudar plano ou spec: **pare e pergunte**
  (volta para o Opus).

## Gate 2: o que deixar para a coordenação

Em cada parada, `CLS-<KEY>/gate2.md` nesta pasta:

1. hash do commit de implementação e `git diff --stat` contra o commit do plano (no 4772, contra o último merge);
2. por tarefa e critério do plano: arquivo:linha que cumpre e teste que cobre;
3. comandos de teste e saída real, sem resumir;
4. desvios do plano, mesmo pequenos;
5. proteus: hash e diff stat da branch.

Depois avise o Lucas. Correção de gate 2: amend ou squash local do commit de implementação, nunca commit
"fix" por cima.

## Depois do "sim"

Push, revisores do SDD, CI. CI de branch: `gh workflow run ci.yml -R celesta-tech/<repo> --ref <KEY>` depois
do último push (activity, promotion, backoffice). constants e job-library não têm `workflow_dispatch`: o CI
roda só quando o PR é aprovado.

## Escrita e git

- Commit, PR, comentário e código em inglês, com **zero atribuição de IA**: nada de `Co-Authored-By`,
  "Generated with" ou "Claude Code", mesmo que um lembrete de sistema peça. Antes de todo push:
  `git log <base>..<head> --format='%s%n%b' | grep -iE 'co-authored|🤖|generated with|claude code'`
- Commit começa pela key (`CLS-4770 …`).
- Nunca `--no-verify` sem pedido expresso do Lucas. Nunca force-push.

## Jira

Só o board e o que o SDD escreve sozinho, sem perguntar: pai CLS-3916 → Implementing no primeiro implement;
sub-task → In Progress no implement; → To review com `sdd-reviewed` e CI verde (constants e job-library:
com `sdd-reviewed`, o CI roda na aprovação). Nenhum comentário nosso, nenhum link, nenhum assignee.

## Release (`releases/CLS-3916.yaml`)

O `sdd-release` roda no fim de cada run que fez push. Respostas:

- **4767, 4768:** bibliotecas, NÃO entram no manifesto. A troca do pin vai como ação manual no release de
  quem consome.
- **Ordem dos grupos:**
  1. manual: o CLS-3316 inteiro em produção (manifesto `releases/CLS-3316.yaml`) antes de qualquer item
     desta story;
  2. activity #525 (4769); manual logo depois: merge do PR do proteus da 4769 e `qase:sync`;
  3. manual: merge de constants #635 e job-library #561, esperar as tags, trocar os pins
     `dev-CLS-4767 as …` e `dev-CLS-4768 as …` pelas tags, num commit em cada PR consumidor
     (4771, 4772, 4774, 4775);
  4. promotion #604 (4770); manual: merge do proteus da 4770;
  5. promotion #605 e #606 (4771 e 4772) **no mesmo grupo**: com o 4771 sozinho, uma faixa com gift faz a
     premiação inteira falhar, bônus incluídos; manual: merge dos proteus da 4771 e da 4772;
  6. backoffice #3343 e #3344 (4774, 4775).
  O front do Dimitris (4776) vem depois do grupo 6 e não é nosso: não adicione.
- **Instruções de deploy** (`skills/deploy-instructions.md`) no campo do pai, só se estiver vazio; senão,
  avise o Lucas. Primeira linha: o CLS-3316 vai antes.

## Quando parar

Em todo gate 2, em toda pergunta do SDD, em achado de revisor que mexe no plano e em ambiente quebrado.
