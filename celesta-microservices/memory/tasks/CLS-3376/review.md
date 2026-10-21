---
name: cls3376-review
description: "Review 2026-10-19 do CLS-3376 (wallet cria carteira no claim), PRs wallet #1897/#1898 e proteus #643, autor Bohdan"
metadata:
  node_type: memory
  type: project
  originSessionId: 0329ea4c-91ef-4a70-9744-3bd9cd5c10f0
  modified: 2026-10-20T07:32:20.605Z
---

Revisor (ticket do Bohdan). Sem matriz e sem plano SDD: a descrição do CLS-3376 é uma story curta, só fala de claim.

Achados levantados em 2026-10-19 (nada postado ainda):
- **Ordem de deploy**: #1898 remove o alias `status: canceled` e exige `currency` no refund; promotion master ainda manda `{status, bonusId}` (WalletClient::refundBonusTransaction). Só a promotion #545 (CLS-3357) manda `action: refund` + currency. Ordem: wallet #1897 → promotion #545 → wallet #1898 + proteus #643. PRs sem descrição.
- **Proteus #643**: só o serviceAPI mudou; `mockAPI.postBonusTransactionRefund` (mockAPI.ts ~757) ainda manda `status: canceled`, usado pelo pcw-34. serviceAPI fixa EUR na moeda.
- `create_wallet_if_missing` vale para a rota inteira: refund numa moeda que o player não tem cria wallet vazia e dá 404.
- Escopo: refund com currency e fim do alias não estão na descrição do ticket → mensagem, não reprovação.

**Atualização 2026-10-20 (wallet `59a6c6012`, promotion `1cec9a7b3`):** o refund passou a ser só `{action, bonusId}`, e a wallet procura o sub_balance pelo bonusId em todas as wallets do player. O claim cria a wallet no handler quando a moeda do body difere, e o `create_wallet_if_missing` saiu da rota. O achado da wallet vazia e o "#1898 exige currency" não valem mais. Continua valendo: #1898 tira o alias `status: canceled` e só entra depois da promotion #545.

Lucas já tinha aprovado o #1898 antes deste review (carimbo, ver [[project_github_approval_vs_real_review]]). Contexto do vai-e-volta da wallet: [[wallet-ownership-shift]].
