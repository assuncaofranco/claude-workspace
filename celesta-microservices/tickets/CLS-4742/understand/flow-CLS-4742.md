# flow CLS-4742 — 2026-11-16 07:33

```mermaid
flowchart TD
    U["BO user"] --> SAVE["salva cenário ou promoção"]
    SAVE --> DBS[("scenario: tabela node, options JSON da ação Offer reward")]
    SAVE --> DBP[("promotion: tabela reward, coluna reward_configuration_id")]

    U --> PAGE["front: página de detalhe da configuração X"]
    PAGE --> CARD["front: card Linked assets"]

    CARD --> BOS["backoffice: POST /domain/id/scenarios com filtro por X"]
    CARD --> BOP["backoffice: POST /domain/id/promotion-configurations com filtro por X"]

    BOS --> SCQ["scenario: lista filtra pelo domínio e por X"]
    SCQ --> DS{"tem ação Offer reward com rewardConfigurationId = X?"}
    DS -->|lê| DBS

    BOP --> PRQ["promotion: lista filtra pelo domínio e por X"]
    PRQ --> DP{"alguma reward da promoção aponta para X?"}
    DP -->|lê| DBP

    classDef changed fill:#fde68a,stroke:#d97706
    class CARD,BOS,BOP,SCQ,DS,PRQ,DP changed
```

Em destaque está o caminho de leitura novo. Nos dois serviços, a lista ganha o filtro "usa X?", o backoffice repassa esse filtro e o front monta o card. É o mesmo desenho que o card de segmento já usa (`SegmentLinkedAssets.js`, que chama essas duas listas com `segmentIds`).

O ticket não grava nada. A ligação com a configuração já é gravada quando alguém salva o cenário ou a promoção, e isso continua igual.

Uma ressalva para o plano: o nome do parâmetro do filtro ainda não existe. Também não conferi o nome exato da tabela-filha das ações no scenario: a entidade `ActionNode` herda de `node` e guarda as `options` numa coluna JSON.
