# explain CLS-3316 — 2026-11-13 15:55

**Objetivo**

Toda vez que uma marca dá dinheiro de graça a um jogador, ela precisa saber depois *por que* deu: fidelidade VIP, compensação, cortesia. Hoje essa resposta pode mudar depois da oferta e está espalhada em duas listas. A CLS-3316 grava o motivo no bônus no momento em que ele é dado, e usa uma lista só por marca. É a continuação do CLS-4163 (motivos de gift).

**Premissas**

1. Marca é um cliente da Celesta, ou seja, um site. No sistema ela é um domínio, e cada uma tem a própria lista de motivos.
2. Todo bônus nasce de uma **configuração de recompensa**: o modelo (tipo, valor) que se cria uma vez no BO e se reaproveita em cada oferta.
3. Hoje o bônus não guarda motivo: ele lê o motivo da configuração. Se alguém edita a configuração, muda o motivo de todos os bônus já dados.
4. Os gifts já usam a lista de motivos por marca que criamos no 4163. As configurações usam outra lista, fixa no código (`loyalty_vip`, `goodwill`…). Resultado: o relatório de recompensas fica partido em dois.
5. Os relatórios dos clientes leem o motivo pelo nome. Por isso a migração cria os motivos antigos com o nome exatamente igual ao que já existe, mesmo que repita um que a marca já tenha.
6. O bônus chega ao jogador por vários caminhos: oferta manual no BO, segmentação, promoção, CSV em lote e cenário.

Fontes:
- `getJiraIssue CLS-3316`: Problem statement, Scope IN e AC (premissas 3 a 6)
- `memory/tasks/CLS-4163/decisions.md`: a lista por marca que já existe para o gift (premissa 4)

**Inferência**

Por isso, o motivo passa a ser copiado para o bônus quando ele é criado, e todo mundo usa a lista da marca:

```
HOJE
  configuração ── motivo (lista fixa no código)
        ▲
        │ lido na hora do relatório
  bônus ┘          → editou a configuração, o passado muda

DEPOIS
  lista de motivos da marca  (a mesma do gift)
        │
        ▼
  configuração ── sugere o motivo ──► oferta (BO, segmentação, promoção, CSV, cenário)
                                        │ quem oferece pode trocar ou limpar
                                        │ copiado na criação
                                        ▼
                                  bônus com o motivo dele, que não muda mais
                                        │
                                        ▼
                                  BigQuery: nome do motivo
```

O que cada sub-task faz nesse desenho:

| Sub-task | Papel |
|---|---|
| 4743 promotion | bônus e configuração passam a guardar o motivo; todo caminho de oferta copia |
| 4744 promotion | migração: a lista fixa vira motivos de cada marca, e os bônus antigos são preenchidos |
| 4745 BO / 4746 front | listas de seleção do motivo e permissões |
| 4747 etl | o relatório passa a ler o motivo do bônus |
| 4748 BO | remove o filtro antigo |

**O que falta**

O cenário. A spec manda incluir na ação de bônus do cenário um campo opcional de motivo, copiado para cada bônus que o cenário cria. Nenhuma sub-task cobre isso:

- a ação de bônus do cenário mora no `celesta-scenario`, e nenhuma das 6 sub-tasks é desse repositório;
- `celesta-scenario` `src/Form/Type/Scenario/Node/ActionNode/OfferBonusOptionsType.php`: a ação de bônus não tem campo de motivo. A de gift já tem (`OfferGiftOptions-ReasonId` em `ScenarioController.php:175`);
- a 4746 (front) fala em "configuration and manual offer", não em cenário.

Ou o split esqueceu, ou alguém cortou o cenário e não tirou da spec. Vale descobrir qual antes do plano.
