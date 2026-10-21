---
name: stacked-pr-merge-trap
description: Mergear PRs empilhados de uma vez faz o código parar na branch base em vez do master — o GitHub mostra Merged e o master não recebe nada; aconteceu no CLS-1872 em 2026-10-14
metadata:
  node_type: memory
  type: project
  originSessionId: 662bddd6-2b1f-4f08-838f-27648f0a4cf5
  modified: 2026-10-14T13:45:45.397Z
---

Numa pilha (`A → master`, `B → A`, `C → B`), mergear os três de uma vez mergeia **cada um na sua
base**. Só o de baixo tem o master como destino. B entra em A, C entra em B, e o master recebe
apenas A.

O GitHub mostra **Merged** nos três, com commit de merge e tudo — porque os três foram mergeados
mesmo, só que no lugar errado. Nada na interface avisa.

O retarget automático para o master só acontece quando a branch base é **apagada** depois do merge.
Mergeando tudo no mesmo minuto, não dá tempo.

**Aconteceu no CLS-1872, 2026-10-14.** Cinco PRs, dois repos. Chegaram ao master só o
`celesta-backoffice#3188` e o `celesta-game#1413` — o pé de cada pilha. O #3189, #3191 e #1414
ficaram parados nas branches. Sintoma: a tela listava as conexões (CLS-2978 e CLS-2980 estavam no
pé) e salvar não fazia nada (CLS-2979 nunca chegou). O PO reclamou que "não está funcionando" e a
primeira hipótese foi bug.

**Como conferir em dez segundos**, e `merge-base --is-ancestor` **não** serve se o repo usa squash
merge — ele responde "não" para código que está lá:

```bash
git diff --stat origin/master..origin/<branch> -- src/    # vazio = o master tem tudo
```

**Como evitar:** mergear um de cada vez, apagando a branch base antes do próximo — aí o GitHub
retargeta sozinho. Ou, se for mergear junto, conferir o campo `base` de cada PR antes:

```bash
gh pr view <n> --json baseRefName,mergeCommit --jq '.baseRefName'
```

**Para destravar depois de acontecer:** não precisa branch nova nem cherry-pick. PR mergeado não
reabre, então abre-se um PR novo da mesma branch com `--base master`. A ponta da pilha carrega tudo
que falta dos tickets abaixo dela.

Relacionado: [[cls1872-review-2026-09-22]], `global/rules/deliverables.md`.
