# elaborate CLS-3316 — 2026-11-16 07:21

**Epítome**

A marca dá dinheiro de graça aos jogadores e precisa saber depois quanto deu e **por quê**: para premiar um VIP, para compensar uma falha, para atrair alguém que acabou de se cadastrar. Sem o porquê, não há como dizer se o dinheiro deu retorno.

Na versão mais simples, o operador da marca dá um bônus e anota o motivo junto. O relatório soma por motivo.

```
operador ──► bônus: R$ 10, motivo "compensação"
                         │
                         ▼
             relatório: R$ 4.000 em compensação neste mês
```

Tudo o que vem abaixo complica essa versão simples. A CLS-3316 existe porque uma dessas complicações foi resolvida do jeito errado.

---

**Camada 1: o mesmo bônus, centenas de vezes**

O bônus de boas-vindas ("100% do primeiro depósito, até R$ 200, com rollover") é dado milhares de vezes. Preencher tudo a cada oferta é lento e gera erro.

A solução foi salvar um **modelo** uma única vez. Cada oferta escolhe o modelo, e o bônus aponta para ele. Esse modelo é a **configuração de recompensa**.

- `celesta-promotion` `Bonus.php:52-53`: todo bônus aponta para uma `RewardConfiguration`, sem exceção

---

**Camada 2: o motivo foi parar no lugar errado**

Se o motivo já está no modelo, ninguém precisa digitá-lo de novo. Foi assim que fizeram: o motivo é um campo da configuração, o bônus não tem motivo próprio, e o relatório busca o motivo na configuração.

O problema: quando alguém edita a configuração, muda o motivo de **todos os bônus que já foram dados** com ela. O passado é reescrito (CLS-3283).

- `RewardConfiguration.php:179-180`: coluna `reason` na configuração
- `Bonus.php`: nenhum campo de motivo
- `celesta-etl` `reward_bonus/bigquery_copy_mysql_to_global.py:98`: `rc.reason`, ou seja, o relatório lê o motivo da configuração

---

**Camada 3: uma lista fixa para todas as marcas**

Os motivos possíveis da configuração são 20 e poucas chaves fixas no código (`loyalty_vip`, `sign_up`, `1st_deposit`, `shop_item`…), iguais para todas as marcas. Uma marca que quer um motivo próprio depende de um deploy.

O gift já resolveu isso no CLS-4163: cada marca cria e apaga os próprios motivos no BO. Só que esse modelo só serve ao gift. Hoje existem duas listas, e o relatório de recompensas fica partido em dois. A lista por marca é o **reward offering reason**.

- `celesta-constants` `RewardConfigurationConstants.php:71-90`: a lista fixa
- `Gift.php:73-74`: o gift já aponta para `RewardOfferingReason`

---

**Camada 4: na maioria dos caminhos, ninguém escolhe nada**

O bônus não é dado só por uma pessoa no BO. Ele chega por cinco caminhos: oferta manual no BO, segmentação (um grupo de jogadores), promoção (o jogador cumpre uma regra), CSV em lote e cenário (automação). Só no primeiro há alguém para escolher o motivo.

A regra nova: no momento em que o bônus é criado, o motivo é **copiado** para ele. Na oferta manual, o motivo da configuração vem sugerido e a pessoa pode trocar. Nos outros caminhos, vem da configuração ou do cenário. Depois de copiado, o motivo não muda mais.

- spec do CLS-3316, Scope IN (Jira, lido em 2026-11-13)

---

**Camada 5: o passado já está escrito com as chaves antigas**

Há configurações e bônus gravados com `loyalty_vip`, e os relatórios dos clientes filtram por esse texto. Trocar a lista simplesmente quebraria esses relatórios.

Por isso a migração cria, em cada marca, um motivo chamado exatamente `loyalty_vip` (e assim para cada chave), mesmo que a marca já tenha um motivo parecido. Depois aponta as configurações antigas para esses motivos, e os bônus antigos para o motivo da configuração deles naquele momento.

- spec do CLS-3316, primeiro item de Scope IN

---

**Síntese: o CLS-3316 inteiro**

```
lista de motivos da marca (camada 3, a mesma do gift)
   │  4744: migração cria as chaves antigas como motivos (camada 5)
   ▼
configuração de recompensa ── guarda o motivo dela (4743 promotion,
   │                            4745 BO, 4746 front)
   │ sugere
   ▼
caminhos de oferta (camada 4)
   ├─ manual no BO ─────── pessoa troca ou limpa   (4745, 4746)
   ├─ segmentação ┐
   ├─ promoção    ├─ copia o da configuração        (4743)
   ├─ CSV         ┘
   └─ cenário ──────────── copia o do cenário       (nenhuma sub-task)
   │
   ▼
bônus com o motivo dele (camada 2 resolvida: editar a configuração não muda mais o passado)
   │
   ▼
relatório lê o motivo do bônus, não da configuração (4747 etl)

4748: o BO remove o filtro que usava a lista antiga
```

**O que falta**

O caminho do cenário. A spec pede um motivo na ação de bônus do cenário, mas a ação mora no `celesta-scenario` (`OfferBonusOptionsType.php`, hoje sem campo de motivo), e nenhuma das 6 sub-tasks é desse repositório. A 4746 (front) também não cita o cenário.
