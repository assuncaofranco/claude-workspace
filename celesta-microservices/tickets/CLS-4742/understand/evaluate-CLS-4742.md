# evaluate CLS-4742 — 2026-11-16 07:47

## Veredito

**Pronto para planejar, com 3 perguntas ao PO antes.** A necessidade de negócio está clara, e a spec e o split estão bem escritos. As lacunas estão nos detalhes, e duas delas mudam AC.

## Onde está

- O pai está em **Split**. Spec e split foram feitos pelo Marcello (comentário de custo de 2026-11-10).
- As 4 sub-tasks estão em To Do, sem plano. **4827 e 4829 estão atribuídas ao Charles Dos Santos**; 4828 e 4830 estão sem dono. Antes de rodar plano, vale alinhar quem pega o quê.
- **Próximo passo:** levar as perguntas abaixo ao PO e depois rodar `/sdd-plan` nas 4. As 4 podem rodar em paralelo, porque o nome do filtro (`rewardConfigurationIds`) já está fixado nas sub-tasks.

## Perguntas ao PO

1. **Permissão.** Pela AC, o card aparece com `PS_BONUS_CONFIGURATION_GET`. Só que as linhas chamam a lista de cenários (`ROLE_OAUTH2_ROLE_SCENARIO`) e a de promoções (`ROLE_OAUTH2_PS_PROMOTION_CONFIGURATIONS_LIST`), e a 4830 manda esconder a linha quando falta o papel, como faz o segmento. Resultado: quem não tem um desses papéis vê "nada depende disto" e desabilita a configuração, que é exatamente o caso que o ticket quer evitar. A pergunta: esconder a linha ou mostrar "sem acesso"?
2. **Erro × "igual ao segmento".** O card de segmento engole o erro: `.catch(() => setAssets({ isLoading: false, data: [] }))` em `SegmentLinkedAssets.js` faz uma falha aparecer como **0**. A AC pede mensagem de erro e também proíbe mexer no card de segmento. Como o componente é compartilhado, a pergunta é se o segmento também ganha o estado de erro ou se ele fica só no card novo.
3. **Quais ativos listar.** O cenário tem soft delete (`Scenario::$deletedAt`) e as promoções têm status. Listar cenário apagado ou promoção desabilitada? A AC diz "igual ao segmento", que herda o padrão de cada lista. Não conferi o que esse padrão devolve.

## Riscos

| Área | Risco | Base |
|---|---|---|
| Dinheiro | Nenhum. O ticket só lê, e oferecer, desabilitar e apagar continuam iguais. | Scope OUT |
| Contrato | O form de filtro do scenario recusa campo desconhecido. Se o BO sair antes e mandar a chave sempre, como faz com `'segmentIds' => $filter['segmentIds'] ?? []`, **a lista de cenários inteira passa a dar 400**. A promotion provavelmente faz o mesmo (os forms dela não declaram `allow_extra_fields`). | `celesta-scenario` `FilterType.php:185` `'allow_extra_fields' => false`; `ScenarioNormalizer.php:719` |
| Deploy | A ordem obrigatória é scenario e promotion → backoffice → front. O Blocks já diz isso, mas precisa estar escrito nas instruções de deploy do pai. | links Blocks 4827/4828 → 4829 → 4830 |
| Dados existentes | Não tem migration. No scenario, o id fica dentro do JSON `options` da ação, sem índice, e o gift grava como `IntegerType`. Falta conferir no banco se há ação antiga com o id como string, que o filtro JSON não acharia. | `OfferGiftOptionsType.php:168`; `ActionNode` coluna `json` |
| Cobertura | Na promotion, toda recompensa é uma linha de `reward` com `promotion_configuration_id NOT NULL`, inclusive as agregadas, então uma consulta cobre "qualquer lista". Falta confirmar que referrer e referee do Refer a friend também são linhas de `reward`. | `Reward.php:33-47` |

Os dois últimos vão para o plano e para o passo do banco, não para o PO.
