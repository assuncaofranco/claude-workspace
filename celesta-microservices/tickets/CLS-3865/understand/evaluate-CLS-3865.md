# evaluate CLS-3865 — 2026-11-16 07:49

O problema de negócio está claro, mas o ticket ainda não está pronto para o plano: falta uma resposta do PO, e a statistics tem um bloqueio técnico que o split não menciona.

**Necessidade de negócio: clara**

Bate com o que concluímos: o gift só conta como custo depois de entregue, pelo valor real. Spec, matriz e split estão escritos no Jira.

**Contradição a resolver antes do plano**

- Spec, AC "Gift recorded before release": concluir um gift antigo não conta de novo, e os períodos antigos não mudam.
- CLS-4938: *"no special rule for older gifts: the feature is not used yet (decided in conversation, 2026-11-12)"*.
- Um dos dois tem de mudar. Se ficar assim, o QA testa o AC da spec e o 4938 entrega sem a regra.

**Perguntas para o PO**

1. Existe gift registrado em produção hoje, e em quais domínios? Isso resolve a contradição acima. Nós não lemos o banco de produção, então a confirmação tem de vir dele ou do TL.
2. A spec fala em status `offered`, e o CLS-3508 diz "from offered or claimed". Esse status não existe no código: o gift já nasce `claimed`. Podemos tirar `offered` do texto?
   - `GiftConstants` no master: só `claimed`
   - `origin/CLS-4434`: `claimed`, `canceled`, com `STATUS_INITIAL = claimed`

**Riscos**

- **Dinheiro:** nenhum saldo se move, porque gift não toca a carteira. O risco é de relatório: generosity é o custo de VIP.
- **Contrato promotion → statistics (o maior risco):** hoje a statistics descarta sem aviso o segundo evento de um mesmo gift. Então o `completed` nunca chegaria ao KPI. O CLS-4938 vai precisar trocar a chave de uma tabela que já está em uso, e o texto dele não diz isso.
  - `Version20261407000003`: `event_promotion` com `PRIMARY KEY (gift_id)`
  - `EventBatchProcessor.php:89`: `ON DUPLICATE KEY UPDATE gift_id = gift_id`, ou seja, não faz nada
  - `config/kpi.yaml:279`: o KPI `gift_claimed` filtra `event_type: created, status: claimed`
- **Ordem de deploy:** a statistics tem de subir antes do Complete da promotion. Se for ao contrário, os gifts concluídos nesse intervalo nunca contam, e o escopo não prevê recálculo.
- **Duas fontes do mesmo KPI:** a statistics alimenta o BO, e o `player_kpi` do terraform-bi (CLS-4939) alimenta o BigQuery. Se subirem em momentos diferentes, BO e BI mostram generosity diferente.
- **Dados existentes:** dependem da pergunta 1. Não conferi se as scheduled queries do BI recalculam períodos passados, porque o terraform-bi não está clonado aqui.
- **"Primeira mudança vence":** a tabela `gift` não tem coluna de versão (`Gift.php`). Como travar fica para o plano do CLS-4941.
- **Permissões:** risco baixo. As chaves técnicas ficam, só o label muda (CLS-4942), então não há migração de grants.

**Dependências: tudo ainda aberto**

| Sub-task | Parte de | Estado |
|---|---|---|
| 4935, 4941 | CLS-4434 | promotion #592 aberto |
| 4940 | CLS-4540 | promotion #591 aberto |
| 4942 | CLS-4437, CLS-3094-CLS-4542 | não conferido |
| 4943 | CLS-4438, CLS-4545 | não conferido |

CLS-3508 está em Preprod ready e CLS-3094 em In preprod. São três níveis de PRs empilhados, a mesma armadilha de merge que já pegou a gente antes.

**Onde está e próximo passo**

- O pai está em Split no Jira e as 10 sub-tasks em To Do. Não existe branch `CLS-49xx` em constants, promotion nem statistics, então nenhum plano foi aberto. O painel mostra plan-draft.
- Próximo passo: levar as duas perguntas ao PO.
- Com a resposta: alinhar a spec ou o CLS-4938, e incluir no 4938 a troca da chave de `event_promotion`.
- Depois: `/sdd-plan`, começando por 4935 e 4938, com o 4938 primeiro na ordem de deploy.

Sua conexão com o Atlassian usa um endpoint V1 que foi descontinuado. Se for o conector oficial, remova e adicione de novo pelo diretório de conectores do Claude. Se for um conector customizado, recrie usando `https://mcp.atlassian.com/v2/mcp`. Se a organização gerencia o conector, peça a troca ao admin.
