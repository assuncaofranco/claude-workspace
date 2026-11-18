# flow CLS-3316 — 2026-11-16 07:23

```mermaid
flowchart LR
  U(["Usuário do BO"]) --> F["backoffice-front: selects de motivo"]
  F --> BO["backoffice: configuração, oferta manual, lote CSV via SQS"]
  BO -->|"POST/PATCH reward-configuration"| RC[("promotion: reward_configuration.reason_id + reward_offering_reason")]
  BO -->|"POST player/.../offer"| OF["promotion: offer"]
  SC["scenario: ação de bônus"] -->|"POST player/.../offer"| OF
  P(["Jogador"]) --> GW["gateway"]
  GW -->|"POST reward/bonuses/claim"| CL["promotion: claim automático, depósito, promoções"]
  PAY["payment"] -->|"DepositJob SQS"| CL
  OF --> D{"reasonId existe, é da marca e não está apagado?"}
  D -->|"não"| E["400, nada gravado"]
  D -->|"sim: grava o enviado, ou vazio"| B[("promotion: bonus.reason_id, backfill na migração")]
  RC -.->|"motivo da configuração"| CL
  CL -->|"copia o da configuração"| B
  B --> ETL["etl reward_bonus, cron"]
  ETL --> BQ[("BigQuery")]

  classDef changed fill:#fde68a,stroke:#d97706
  class F,BO,RC,OF,SC,D,E,CL,B,ETL changed
```

Em destaque está onde o motivo passa a ser escolhido, validado, copiado e gravado: hoje ele existe só na configuração (`RewardConfiguration.php:179`), e o etl o lê de lá (`bigquery_copy_mysql_to_global.py:98,107`).

Todo bônus nasce no `RewardOfferService` da promotion, por duas entradas: o endpoint `offer` (BO manual, lote CSV via `OfferFreeBonusHandler` e cenário) e o claim (gateway, e `DepositJobHandler` / `SuccessfulDepositJobHandler` no depósito).

O `scenario` também está em destaque porque a spec o inclui, mas nenhuma das 6 sub-tasks é desse repositório.
