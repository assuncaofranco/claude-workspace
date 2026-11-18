# evaluate CLS-3316 — 2026-11-16 07:47

**Onde está:** o pai está em **Split** (assignee Francisco). Das sub-tasks, a 4746 (front, Dimitris) está In Progress e as outras cinco em To Do, todas com você. Nenhum plano foi escrito ainda: não existe branch `CLS-474*` em promotion, backoffice, front, etl ou scenario (conferido com `git ls-remote`). No Jira há um único comentário, o do custo do split.

**Pronto para começar?** A necessidade de negócio está clara, e a spec é boa. O problema é que **as sub-tasks contradizem a spec em quatro pontos**, e a 4746 já está sendo feita em cima de um deles. Eu não rodaria nenhum `sdd-plan` antes de o PO responder: o plano lê o pai e a sub-task, e onde os dois divergem ele escolhe um sozinho.

**Divergências entre a spec e o split**

| # | Spec (pai) | Sub-task | Prova |
|---|---|---|---|
| 1 | migração cria **todos** os motivos antigos | 4744 cria **13** | `RewardConfigurationConstants::REASONS` tem 31 chaves, e o front ainda traduz mais 10 marcadas `[EXPIRED]`/`[OBSERVED]` (`en.js`, 41 chaves `reward.form.reason.*`) |
| 2 | nome = a chave exata (`loyalty_vip`) | 4744: nome legível ("Loyalty VIP"), e a 4747 converte de volta para chave | descrições do pai e da 4744 |
| 3 | oferta manual vem **pré-preenchida** com o motivo da configuração e troca junto com ela | 4746: "none by default" | AC do pai × descrição da 4746 |
| 4 | o cenário tem select próprio, e o bônus recebe **o motivo do cenário**, nunca o da configuração | 4743: "scenario… copy the configuration's reasonId"; nenhuma sub-task no `celesta-scenario` nem select de cenário na 4746/4745 | `OfferBonusOptionsType.php` sem motivo; `PromotionClient.php:51` do scenario chama o mesmo `offer` |

O formulário de oferta de **gift** com pré-preenchimento também está na spec e em nenhuma sub-task.

**Perguntas para o Francisco** (prontas para colar):

1. migration seeds 13 legacy reasons, but promotion accepts 31 keys and the BO still labels 10 expired ones. should we seed every key found in the data? configs with the other keys would lose their reason in BigQuery
2. seeded names: the raw slug (`loyalty_vip`, as the spec says) or a label like "Loyalty VIP" (as CLS-4744 says)?
3. manual bonus offer: should Reason start with the config's reason, or empty?
4. is the scenario bonus action still in scope? if so it needs scenario and front sub-tasks, and it should get the scenario's reason, not the config's
5. gift offer form pre-fill: which sub-task owns it?

**Riscos**

- **Dinheiro (indireto):** o motivo não muda o valor do bônus, mas a validação nova pode **barrar uma oferta**. Os caminhos que só copiam o motivo (depósito, promoção, segmentação) não podem rejeitar nada, nem quando o motivo da configuração foi apagado. Se rejeitarem, o jogador fica sem o bônus de depósito.
- **Contratos:** o `offer` da promotion ganha `reasonId` (chamado por BO, bulk e scenario). O `reason` antigo deixa de ser obrigatório (`RewardConfigurationType.php:68`). As respostas de configuração e de bônus ganham o motivo. Proteus com payload de `reason` vai precisar de ajuste.
- **Dados existentes:** chave fora das 13 fica sem motivo, e a 4747 passa a gravar null no BigQuery para esses bônus. Também falta saber o tamanho da tabela `bonus` para o backfill, que pela regra do 4163 deve ir como SQL na DI, em lotes. Nada disso está verificado no banco ainda.
- **Deploy:** a ordem é 4743 → seed/backfill 4744 → **4747 junto ou antes da 4745** → 4746 → 4748. Se o BO parar de mandar a chave antiga antes de o etl ler o motivo novo, os bônus das configurações novas vão para o BigQuery sem motivo. A 4746 está andando, mas só pode ir para produção depois de 4743 e 4745.

**Próximo passo:** mandar as 5 perguntas ao Francisco e avisar o Dimitris sobre o ponto 3 antes que ele feche a 4746. Enquanto isso, dá para contar as chaves que existem de fato em `reward_configuration.reason` no pp1 (`db-query`, somente leitura). Com as respostas, ajustar o pai e as sub-tasks, e aí rodar `/sdd-plan` da 4743 e da 4744 em paralelo.
