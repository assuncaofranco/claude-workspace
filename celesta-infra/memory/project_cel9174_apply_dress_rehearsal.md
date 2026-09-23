---
name: project-cel9174-apply-dress-rehearsal
description: Como fazer o primeiro apply automático do lrgi-terraform sem risco — ensaio com o interruptor desligado
metadata: 
  node_type: memory
  type: project
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-16T12:16:57.468Z
---

Plano combinado com o Lucas em 2026-09-16 para o primeiro apply automático do
`lrgi-terraform` (CEL-9174). Ele quis que o **pipeline** aplicasse as mudanças do
CEL-8733, em vez de aplicá-las à mão antes.

```
TL cria a variable TERRAFORM_APPLY_ENABLED com valor "false"   (precisa de admin)
      │
merge do PR #51
      │
      ▼
apply.yml roda de verdade: busca o plano no S3, passa pelo portão de drift,
imprime o plano completo no log, lê "não é true" e PARA
      │
      ▼
Lucas lê o log. Se mostrar exatamente as 5 mudanças, vira a variable para "true"
e um PR qualquer dispara o apply real.
```

**Por que isso é melhor que o "apply de plano vazio" que tínhamos desenhado:** o
merge do #51 já ensaia a corrente inteira com o **conteúdo real** do 8733, sem
tocar na AWS. Sobra sem teste apenas a chamada `terraform apply` em si, que é o
pedaço mais batido do terraform e o único que não é fiação nossa.

**Por que o risco é aceitável:** o plan é 3 mudanças no `iam/` e 2 no `backend/`,
todas `update in-place`, zero destroy, e **nenhuma toca a role do CI** — que era
o risco de o pipeline revogar o próprio acesso. O `backend/` é só proteção
aditiva (PITR, criptografia, bucket policy).

**Gotcha a lembrar na hora:** se o apply falhar no meio, o state muda e o plano
salvo fica obsoleto. Re-rodar não funciona, o terraform recusa. A saída é PR novo
e aprovação nova.

Ver também [[project-cel8734-drift-schedule-check]] e
[[project-cel8469-lrgi-terraform-audit]].
