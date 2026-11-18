---
name: preprod-deposit
description: "Como fazer um depósito real de teste em preprod pela porta do jogador (gateway POST /payment), com Newman — onde estão o cartão, o gerador da coleção e as armadilhas"
metadata:
  node_type: memory
  type: reference
  originSessionId: ce1ff9bf-ec84-4901-ba43-d9604fdb7cab
  modified: 2026-10-27T08:46:57.215Z
---

Depósito de teste em preprod, pelo fluxo de verdade (gateway → payment → wallet → `DepositJob` para a
promotion): **`POST {{baseUrl}}/payment`** com o token do player. No OpenAPI do gateway é o "Deposit",
tag `Payin` (`celesta-gateway src/Deposit/Controller/PaymentController.php`).

- **Cartão e `paymentConfigurationId`:** no vault, `~/.claude-secrets/celesta-preprod.md`, seção
  "Depósito de teste pelo gateway". Nunca na coleção, nunca aqui (esta pasta é versionada).
- **Coleção pronta:** `claude-workspace/celesta-microservices/postman/CLS-3676/gen_pp1_deposit.py` gera
  token → saldo → `POST /payment` → saldo. Os valores entram por `--env-var` na hora de rodar.
- **Token do player:** `{{baseUrl}}/oauth/2.0/token`, com `deviceInformation`. `/oauth/token` dá 404.
- **Sem `bonusIds`** quando o teste é de promoção deposit_tier: esse campo aciona o "clamar bônus no
  depósito" e mistura os rewards. Com `bonusIds` é outro teste (claim no depósito).
- **Crédito é assíncrono:** a leitura do saldo logo depois da chamada ainda mostra o valor antigo.
- Cada chamada é uma transação nova; não serve para provocar redelivery. Para mandar o mesmo depósito
  duas vezes, só empurrando o `DepositJob` na fila (a automação do QA faz isso).

Conferido em 2026-10-27 no pp1, `lucastest`, domínio 56: 200, saldo 100,30 → 110,30. Origem: o
Francisco, no CLS-3676 ([[cls3676-decisions]]). Ver [[preprod-branch-deploy]].
