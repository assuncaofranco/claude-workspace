---
name: payment-paytech-environments
description: "Paytech: a API só aceita IP liberado (o local, mesmo na VPN, não chega); em pp1 a configuração 426 aponta para a Paytech de produção; cartões de teste do sandbox"
metadata:
  node_type: memory
  type: project
  originSessionId: 62088cdd-c327-4fdb-8c35-d9d5e7834bae
  modified: 2026-11-12T18:29:11.696Z
---

Visto em 2026-11-12 (CLS-4779).

- **IP liberado.** A chave do sandbox (loja 121) que está no banco local é válida, mas a Paytech responde
  401 "IP address … is not whitelisted" para o IP de saída da máquina do Lucas, inclusive na VPN. Teste
  real da Paytech só a partir de preprod, e mesmo lá ninguém fez um depósito Paytech até essa data.
- **pp1, domínio 56:** configurações 424 (sandbox, os 6 cartões, visa = payment configuration 7875) e
  425 (sandbox, domínio 213). A **426 aponta para `engine.tx.tech`, produção**, com outra chave, e é a
  única com Apple Pay. Nunca testar nela.
- **Cartões de teste do sandbox** (doc da Paytech, aba Testing): `4000 0000 0000 0408` aprova sem 3DS
  (bom para Newman), `4000 0000 0000 0416` recusa sem 3DS; os outros pedem 3DS. Refund no sandbox até
  10000.

**How to apply:** teste da Paytech é em preprod, pela coleção em `tickets/CLS-4779/`. Ver
[[global-write-pilot]].
