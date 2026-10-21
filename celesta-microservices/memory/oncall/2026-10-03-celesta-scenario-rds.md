# 2026-10-03 — Celesta Scenario RDS below 10% Freeable Memory (Prod)

Alerta P2 às 01:36 (hora do Lucas), sem histórico no canal. Instância `celesta-prod-1-scenario`: `db.t4g.large` (8 GB), MySQL 8.4.10, Multi-AZ, parameter group `terraform-20251125133849806400000001`.

**Balde:** nenhum dos cinco. Não é vazamento: é o cache esquentando depois de troca de instância.

**Causa (confirmada pelas métricas):**
- Em 2026-09-24 13:52 UTC houve switchover blue/green. A instância nova começou com o buffer pool vazio, ~6 GB livres.
- O `innodb_buffer_pool_size` está em `engine-default`, 3/4 da RAM (~6 GB). A memória livre cai enquanto o cache enche e para no limite.
- O blue/green de 24/09 foi o **aumento de `db.t4g.medium` (4 GB) para `db.t4g.large`** (CEL-9313, commit `67a5aca7` em `celesta-casino-terraform`, Lucas Azevedo). A antiga, menor, passou setembro com 44 a 500 MB livres e 1,7 a 2,8 GB de swap, sem cair. Ela era pequena demais, e por isso foi trocada.
- **Não comparar como se fosse a mesma classe.** Primeiro eu disse que era, e estava errado. Pela conta grosseira com os números da antiga, a nova pode passar a usar swap quando o cache encher. Swap sem latência alta não é emergência.
- Na nova, a memória livre caiu de 6 GB para 385 MB em 9 dias, com swap 0 e conexões estáveis (10–18).
- O monitor com limite de 10% (~800 MB) fica abaixo do patamar normal dessa classe. Provavelmente ele é novo ou estava silenciado, porque não disparou em setembro.
- Hipóteses descartadas:
  - código novo (actions do scenario): o cache da aplicação mora nos pods, e as conexões não mudaram;
  - mudança de 2026-09-29 no parameter group: o único parâmetro de memória definido por alguém é `performance_schema=1`, que é estático, e não houve reboot depois.

**Atualização 2026-10-05:** o swap apareceu em 2026-10-03 por volta das 15:30 UTC e subiu em linha reta, ~18 MB/h, chegando a 512 MB em 2026-10-04 às 20:00 UTC. A memória livre ficou parada em ~150 MB, e a latência de leitura em ≤ 10 ms. **O cache explica só a queda depois do blue/green.** O swap crescendo com o buffer pool já no teto é memória **fora** do cache crescendo. Janis Gruzis atribui isso a performance do `session_step`, que vem acontecendo há quase um mês (CLS-2902, Team C), e abriu um expedite em 2026-10-05. Os dados concordam com ele.

**2026-10-06, suspeito no código (hipótese, não confirmada):**
- O Performance Insights mostra o banco quase parado (carga média ~0,005 sessões ativas em 2 vCPUs). O swap sai a 3–10 KB/s e volta a ~0,3 KB/s: são páginas frias.
- O query cache está descartado: foi removido no MySQL 8.0, e o banco roda 8.4.10, sem parâmetro `query_cache`.
- Na instância antiga, a memória livre caiu de ~450 para ~50 MB e o swap saltou de 1,8 para 2,8 GB **entre 14 e 16/09**. No mesmo 14/09 o scenario foi para produção com a v1.175 (08:09 UTC) e a v1.176 (12:41 UTC) (`celesta-argocd`, overlay `prod-1`).
- A v1.176 traz o CLS-2396 (Charles Santos): `SessionStepRepository::reportPlayers` faz `JSON_SET(node_data, ...)` com **um path por jogador**, `completeIfFullyReported` usa `JSON_LENGTH(JSON_EXTRACT)` sobre listas de jogadores, e `resolveParentSteps` monta um `CASE id WHEN` de tamanho variável. O formato da query varia com o tamanho da população, e o MySQL remonta um JSON cada vez maior a cada update. Isso casa com memória crescendo fora do buffer pool, seja por fragmentação, seja pelos digests do performance_schema.
- **Confirmar com o DevOps:** rodar `sys.memory_global_by_current_bytes` duas vezes, com horas de intervalo, e ver qual categoria cresce.

**Desfecho (thread, 2026-10-06/07):**
- Janis Gruzis abriu o expedite **CLS-3377** e fez a RCA, com um artifact do Claude dele.
- Novo blue/green em 2026-10-07 às 07:45, adicionando um índice em `updated_at`. Incidente resolvido às 08:16. Janis deixou um lembrete para checar em 5 dias, porque da vez anterior a memória voltou a cair em 9 dias.
- **Explicação aceita na thread, levantada pelo Ghislain:** o performance_schema guarda dados **por IP de cliente**, e cada execução de cronjob sobe num pod novo com IP novo. Em prod-1, o `scenario_job_scheduled_event` roda a cada minuto (`* * * * *`, overlay `prod-1` no `celesta-argocd`), o que dá ~1.440 IPs novos por dia. **Isso explica melhor que a minha hipótese o swap subindo em linha reta e constante com o banco quase parado.** Minha hipótese do `JSON_SET` (CLS-2396) ficou só como possível explicação para o degrau de 14/09.
- **Em aberto, fora do escopo do oncall:** 2.158 mensagens de sessão falharam por ~20 min depois do switchover, porque os workers ficaram presos na instância antiga (blue), em modo read-only. Não se confirmou se o retry delas teve sucesso.

**Saída:** reportar e vigiar o `SwapUsage` no fim de semana (sábado, domingo e o feriado de segunda). Escalar para o DevOps se o swap subir junto com a latência.

**Alavancas de emergência** (quem executa é o Lucas, nunca eu):
- **Reboot com failover**, pelo console ou por `aws rds reboot-db-instance --profile celesta-prod-1 --db-instance-identifier celesta-prod-1-scenario --force-failover`. Fica ~1 min fora do ar, esvazia o cache e ganha alguns dias. Não passa pelo Terraform.
- **Aumentar a classe**, só pelo Terraform: `instance_class` em `celesta-prod/prod-1/rds.tf`. Com `db_blue_green_update_enabled = true` e `apply_immediately = true`, o apply faz um novo blue/green na hora. O repositório é do DevOps: escalar para o Lucas Azevedo, não rodar o apply. Agravante, segundo a mensagem do commit `67a5aca7`: o blue/green foi feito **à mão** e o estado do Terraform ainda aponta para a `old1`, então um apply com `-target` nesse módulo pode tentar mexer na instância errada.

**Histórico que eu não achei no índice:** o mesmo commit diz que o aumento de máquina foi a resposta a um "scenario memory incident" em 2026-09-24. Buscar no Slack (CEL-9313) antes de concluir qualquer coisa num próximo alerta deste banco.

**Checar no dia útil:** ajustar o limite do monitor para essa classe, ou trocar o sinal para swap ou latência.
