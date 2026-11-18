---
name: github-approval-vs-real-review
description: Um APPROVED no GitHub não quer dizer que houve review na Celesta — costuma ser só o carimbo pedido para destravar o CI; o review de verdade acontece depois que Lucas move o ticket para Review no board do Jira
metadata: 
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-11-16T10:21:49.204Z
---

**Mudou com o CEL-9751 (SSD-954):** o CI **não roda mais por aprovação**. Numa branch ele só roda
por `workflow_dispatch` (`gh workflow run ci.yml -R celesta-tech/<repo> --ref <branch>`, ou o botão
no Actions); o marcador `[run-ci]` no commit, que existiu de 12 a 13/11, foi revertido
(`CEL-9751-rollback-keep-dispatch`, 2026-11-13, em todos os repos). Push comum sai com todos os jobs
`skipped`; master e tags `v**` rodam em todo push. Release e deploy continuam só no master. Quando
disparar está em `global/skills/ticket-story.md`.

Antes disso, o desenvolvedor **não podia rodar o CI no próprio PR**: a pipeline só disparava com uma
aprovação, então os devs aprovavam os PRs uns dos outros, e essa aprovação existia para destravar o CI,
não porque alguém leu o código. Aprovações antigas continuam sendo lidas assim. Vale nos dois sentidos: nos PRs do Lucas e nos que ele revisa
(CLS-3290, 2026-10-12: duas aprovações e um review dele DISMISSED, nenhum era review). Toda aprovação
anterior ao review do board é ignorada, não reportada.

**O review de verdade começa quando ele move o ticket para _Review_ no board do Jira.** É outro momento,
com outra pessoa, e é o que vale.

**O que isso muda na leitura dos sinais do GitHub:**

- `reviewDecision=APPROVED` não é evidência de revisão. Não tratar como "já foi revisado".
- Aprovação anterior ao head atual **não é um problema a reportar**. Em 2026-09-22 (CLS-1872) eu levantei
  que os 5 PRs estavam aprovados sobre código velho e recomendei avisar os revisores commit a commit —
  recomendação inútil, porque aquelas aprovações nunca foram review. O sinal certo a verificar é o CI,
  não a data do carimbo.
- Quem aprovou por esse motivo não deve ser incomodado com "o que mudou desde a sua aprovação".

**O que continua valendo verificar antes de mandar para Review:** CI verde de verdade (os jobs
`tests/phpunit`, `tests/codestyle`, `tests/openapi-lint`, `build`, `migration`, não só os gates do
Datadog), comentários abertos do Copilot/Datadog respondidos, branches em dia com o master, e nenhuma
atribuição de IA em lugar nenhum (ver a regra em `~/.claude/CLAUDE.md`).

**Efeito colateral a lembrar:** como a proteção de branch não descarta review obsoleto, esses carimbos
deixam o PR tecnicamente mergeável sem que ninguém tenha lido. Vale mencionar uma vez se alguém for
mergear antes do review do board — não vale insistir.

Relacionado: [[cls1872-review-2026-09-22]], `global/rules/writing.md`.
