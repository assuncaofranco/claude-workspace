# debate CLS-3865 — 2026-11-16 07:32

**Objetivo**

Um presente só deve contar como custo do jogador depois de entregue, e pelo preço que de fato custou. Hoje ele conta no momento em que é anotado, pelo valor estimado. O CLS-3865 corrige isso.

**Premissas**

1. Gift é a anotação de um presente físico entregue fora do sistema, como ingresso, jantar ou eletrônico para VIP. Não credita carteira nem notifica o jogador.
   ↳ memória `tasks/CLS-2594-CLS-3055/review.md`
2. Hoje o gift nasce `claimed` e esse status é final. O mesmo status vale para "acabei de anotar, falta encomendar" e para "já entreguei".
   ↳ CLS-3865, Problem statement
3. Entre a anotação e a entrega o preço real pode mudar, e o presente pode nem chegar (cancelado, CLS-3508).
   ↳ idem
4. Generosity e os KPIs de gifts (CLS-2957) medem quanto a operadora gastou com o jogador, e hoje somam os gifts `claimed`. Então o relatório de custo de VIP usa valores provisórios.
   ↳ idem, e compendium *Rewarding* §3.2
5. Os gifts que ainda faltam encomendar ficam espalhados na página de cada jogador. Quem encomenda não tem uma fila única para trabalhar.
   ↳ idem

**Inferência**

Por isso, o gift ganha um passo a mais na vida dele, e o custo só é contado no último passo:

```
anotado ──► claimed  ("falta encomendar")
              │   aparece na página nova "Gifts to order":
              │   fila do domínio, do mais antigo para o mais novo
              │
              ├─ Edit value ── preço mudou: ajusta o valor (a moeda não muda)
              │                o KPI ainda não conta nada
              │
              ├─ Complete ───► completed  (final, nenhuma ação depois)
              │                 conta UMA vez em generosity e nos KPIs,
              │                 no período da conclusão, pelo valor final
              │
              └─ Cancel ─────► canceled  (CLS-3508): não conta em lugar nenhum
```

Os períodos anteriores ao release ficam como estão. Um gift antigo já foi contado quando foi anotado, então concluí-lo agora não conta de novo.

O resto do ticket serve a esse fluxo:
- as permissões *View gifts* / *Edit gifts* separam quem só vê de quem age;
- os eventos `gift_value_edited` e `gift_completed` guardam quem fez e quando, porque o ticket decidiu não criar os campos `completed_by` e `completed_at`;
- cada mudança de status chega à statistics, que é de onde os KPIs leem.
