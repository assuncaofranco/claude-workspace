# CLS-4779 — passos do SDD

Refund automático de depósito por cartão na Paytech. Story em Ready, sem split. A spec já existe;
`sdd-spec` recusa Story.

| # | Comando | Para em | O que avaliar |
|---|---|---|---|
| 1 | `/sdd-split CLS-4779` | sub-tasks criadas | um repositório por sub-task, ordem dos Blocks, cleanup |
| 2+ | `/sdd-plan` e `/sdd-implement` por sub-task | rascunho / pedido de push | como no CLS-1214 |

## Feito

- 2026-11-12: os $0.37 da emenda do plano entraram no custo do implement do 4933 (`sdd-plan` $5.34, 2 runs).
- Proteus #807: `pcp-69` provisório; o CI do payment não logou id do Qase. Renomear quando o case aparecer.
- Worktree `celesta-qaa-proteus-CLS-4933` (irmã do clone) criada para não tocar no clone principal, que está em CLS-4540 com trabalho de outra sessão.
