---
name: preprod-branch-deploy
description: "Como uma branch sobe para um preprod da Celesta antes do merge — Jenkins, pelo nome da branch; o merge em master faz deploy automático"
metadata:
  node_type: memory
  type: reference
  originSessionId: ce1ff9bf-ec84-4901-ba43-d9604fdb7cab
  modified: 2026-11-12T12:14:14.037Z
---

Para testar em preprod **antes do merge**, o Lucas sobe a branch pelo **Jenkins**, informando o **nome
da branch** (ex.: `CLS-4053`), no preprod escolhido (pp1, pp2…). Depois do merge em `master` o deploy é
automático, então o teste em preprod tem de acontecer antes do merge, nunca depois.

O CI do PR roda primeiro; o deploy no Jenkins vem depois.

**O gate do Jenkins** (etapa "Check Github Actions - CI", `libraries/vars/checkCIStatus.groovy` no
`celesta-jenkins-config`) exige duas coisas: o **último review não-comentário do PR estar `APPROVED`**
e o run mais recente da branch ter terminado com `success` (ou falhado sem o job `tags` falhar). Todo
push no PR deixa a aprovação `DISMISSED`, e aí o deploy falha nessa etapa mesmo com o CI verde. O nome
da etapa engana. A ordem é: último push (com `[run-ci]`), CI verde, aprovação de novo, deploy, sem push
no meio. Visto em 2026-11-12, BO #3307 (CLS-4035).

**Como usar:** no passo de preprod do fluxo de ticket (skill `preprod-test`, "confirmar o deploy"),
perguntar ao Lucas em qual preprod ele subiu a branch pelo Jenkins; não propor "testar depois do
merge". Não tenho acesso ao Jenkins: quem dispara é ele.

Visto em 2026-10-27, CLS-4053 ([[cls3676-decisions]]). Ver também [[one-preprod-per-check]].
