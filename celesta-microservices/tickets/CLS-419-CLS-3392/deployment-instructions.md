# CLS-419-CLS-3392 — Deployment instructions

## Ordem

```
1. Merge celesta-job-library #538 (CLS-419-CLS-3433) → tag v3.134
2. celesta-statistics #1009 (CLS-419-CLS-3353-api) e celesta-promotion (CLS-419-CLS-3392):
   trocar dev-CLS-419-CLS-3433 por ^3.134 no composer
3. Deploy celesta-statistics #1009
4. Deploy celesta-promotion (CLS-419-CLS-3392)
```

**Regra curta: statistics antes do promotion. Nunca o promotion sozinho antes.**

Sem migration no promotion, sem variável de ambiente nova, sem fila nova.

---

## Por quê

O promotion passa a publicar `GiftEventJob` na fila `statistics-kpi` a cada gift criado
(`GiftEventSubscriber`). Quem lê essa fila é só o statistics. Nenhum outro serviço publica ou consome
esse job.

| Estado | O que acontece |
|---|---|
| promotion novo, statistics velho | o statistics velho não conhece a classe `GiftEventJob`; o receiver SQS apaga a mensagem que não consegue decodificar (`symfony/amazon-sqs-messenger` `AmazonSqsReceiver.php:54-57`). **Os gifts criados nessa janela nunca entram no KPI.** O BO funciona normal. |
| statistics novo, promotion velho | nada é publicado; o statistics só não recebe gifts. Inofensivo. |

## Rollback

Ordem inversa: **o promotion volta primeiro**. Se só o statistics voltar com o promotion novo no ar,
cai no estado "promotion novo, statistics velho" e os gifts se perdem.

Promotion voltando sozinho é seguro: para de publicar.

## Infra

- O transport novo usa a conta e o prefixo que o promotion já tem como `SQS_QUANTA_*`. É onde o
  statistics lê `statistics-kpi` em todos os ambientes (`celesta-argocd-parameters/<env>/{promotion,statistics}/parameters.yaml`;
  prod-1: `954607206481`, `celesta-prod-`). A fila já existe, a wallet publica nela.
- **A confirmar com DevOps:** a chave `SQS_QUANTA_*` do promotion tem `sqs:SendMessage` na fila
  `statistics-kpi`? Hoje ela só publica em `backoffice` e `notification`, e a policy da conta quanta
  não está nos repositórios de infra a que temos acesso. Sem a permissão, o envio falha depois da
  resposta e o gift não entra no KPI, sem erro visível no BO.

## O que observar depois

- Oferecer um gift pelo BO: deve aparecer uma linha em `event_promotion` no statistics com
  `event_type = created`, `status = claimed`, e o `giftClaimedAmount` do jogador sobe depois do
  próximo `kpi:process-events`.
- Logs do promotion sem erro de SQS para `statistics-kpi`.

## Fora deste deploy

Gifts criados antes do deploy não são reenviados (sem replay/backfill, fora do escopo do CLS-3392).
