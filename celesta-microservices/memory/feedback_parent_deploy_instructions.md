---
name: feedback-parent-deploy-instructions
description: "O Marcello faz o deploy lendo só a DI do ticket pai; a nossa DI entra lá, junto com a dos outros devs"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 831bafd1-67ef-47f1-bf15-3ce9d4e5441e
  modified: 2026-11-04T10:36:58.709Z
---

Quem faz o deploy (Marcello) lê as instruções de deploy e de rollback **do ticket pai**, não das
sub-tasks. Toda DI nossa também vai para o pai, encaixada no que já estiver lá: ler pai e irmãos
antes, manter os passos dos outros devs (merge de QA, script, espera) e montar a ordem completa.

**Why:** Lucas, 2026-11-04 (CLS-3282-CLS-4163): o pai pode ter coisa de outro dev que a nossa
sub-task não conhece, e a DI só na sub-task não chega a quem aperta o botão.
**How to apply:** passo a passo no skill `deploy-instructions`, seção "Onde vai". Ver
[[cls4163-decisions]].
