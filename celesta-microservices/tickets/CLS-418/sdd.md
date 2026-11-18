# CLS-418 — passos do SDD

KPIs de player servidos só pela Statistics. Task em Split, 7 sub-tasks de A, B e C.

Bloqueado até:
- confirmar quais sub-tasks são nossas: 3522, 3523 (statistics), 3525, 3528 (payment); a 3526 tem
  `{B}` no título e A-Team no componente;
- o Viorel responder as duas perguntas abertas da spec: moeda não padrão no BO; dropar as colunas do
  payment agora ou depois.

Spec no formato antigo (Summary/Background/Functional Requirements). O primeiro `sdd-plan` avalia se
ele aceita.

## Estado

- 2026-11-13 13:03: worktrees `celesta-{statistics,gateway,payment,backoffice,segment}-CLS-418/` em origin/master.
  Onda 1 (3522, 3523) com rascunho em `drafts/`; 3524 e 3525 rodando; 3526 e 3527 seguram até as respostas
  do 3522 e do 3523 (contrato em cadeia, mesma lição do CLS-1214). Verificação da onda 1 contra o código em
  subagente.
- Achados do 3522: generosity já no master (CLS-419-CLS-3353); eventos de saque já chegam na statistics.
- 2026-11-13 ~13:20, parada para reiniciar o sistema:
  - 3524 com rascunho (Q1 moeda = mesma pergunta do Viorel sobre moeda no BO; responder junto). 3525: conferir
    se o rascunho existe em `drafts/`; se não, o agente morreu no reinício e precisa ser reaberto.
  - Verificação da onda 1 feita (subagente): 3522 e 3523 "prontos depois de correções". A mensagem de correção
    foi escrita na coordenação e NÃO foi enviada. Principais: `requested_withdrawal` por `event_type: created`
    (limpeza de 14 dias roda em prod); sem teto de 1000 ids no 3523 (cron roda `--batch_size=2000`); Q6 do 3523
    tem drift de dia entre o tempo real (Payment) e o sync (Statistics) → vai ao Viorel.
  - 3526 e 3527 seguram até as respostas do 3522 e 3523.
- 2026-11-13 (depois do reinício): 3525 com rascunho. 3528 aberto às 13:13, sem rascunho em `drafts/`.
  Conferido no payment origin/master: `successful_payin_amount`/`_count` só são escritos pelo
  `TestUpdatePayInAmountCommand` (o `TransactionSubscriber::emitKpiJob` manda KPIJob, não grava a coluna) →
  em prod o endpoint devolve sempre 0. Ligar na Statistics muda o valor de 0 para o real: o FR8 ("resposta
  inalterada") não se cumpre de nenhum jeito. Vai ao Viorel junto com dropar colunas e a regra de moeda
  (3524-Q1 soma moedas × 3525-Q1 moeda do CRM).
