---
name: oncall-2026-11-06-celesta-segment-rds
description: "RDS celesta-prod-1-segment CPU > 80% (monitor 126748113) depois do ASG segment-worker ir de 3 para 6; não baixar o ASG, a fila volta a acumular"
metadata:
  node_type: memory
  type: project
  originSessionId: 1a8e9ad7-6709-4025-814c-1806b867af7b
  modified: 2026-11-07T23:44:16.073Z
---

**Alerta:** `Celesta RDS celesta-prod-1-segment CPU above 80.0% (Prod-1)`, monitor 126748113. Disparou 17:48 e 20:06 UTC de 2026-11-06.

**Balde:** causa conhecida (mudança de capacidade), não fila nem código.

**Causa:** em 05/11 ~21h UTC o Ivan subiu o ASG `segment-worker-autoscale-group` (conta legada) de 3 para 6 (PD #2764). Cada worker roda a query de backlog em `segment_player_evaluation` (COUNT DISTINCT player_id, MAX(id), oldest_age_seconds): ~15 → ~30 execuções/s. A tabela não cresceu; à tarde o backlog sobe com o tráfego e cada execução fica mais cara. As 3 máquinas novas não mandam trace.

**Evidência (Datadog, 30 min):**
- CPU mesmo horário, ontem (3 workers) × hoje (6): 17:00 47 × 73, 19:30 44 × 79, 20:00 49 × 81; em 10 min chegou a 90 às 20:10. Sobe com a curva do tráfego, não descola dela.
- `celesta-prod-segment-balance.fifo` (o nome no DD tem o prefixo `celesta-prod-`): ontem com 3 workers a idade da mais antiga foi 282 s (20:00) → 1072 s → **1864 s (21:00)**, 4k visíveis; hoje com 6, 7–10 s o dia todo.

**Decisão:** reportar e esperar. Randy decidiu não reverter (thread no Slack, p1793950601880639). Baixar o ASG troca um alerta de CPU sem impacto pelo backlog de 30 min que gerou o PD #2764, justo no horário em que ele aconteceu.

**Desfecho (~20:30 UTC):** o Ghislain Gaucher respondeu na thread que a instância está pequena para o volume e criou um Blue/Green para subir a classe (era db.t4g.large). O downtime no grupo do segment, que eu tinha sugerido, deixou de fazer sentido. A carga por worker continua sendo o multiplicador, então o ticket abaixo segue válido.

**Origem da query:** é o loop do `player-segment:update` (`fetchPlayerScopes`), rodando em cada máquina do ASG. Só dorme quando não tem nada pendente. No PI das 3h: 3.88 AAS em 2 vCPU; essa query + o `SELECT id` seguinte ≈ 70%; 6 IPs com ~0.6 cada.

**Histórico que o Ghislain lembrou:** o CLS-2054 (jul–ago) teve deadlocks entre workers de drain concorrentes, corrigido com delete por PK e índices de cobertura; zero `DeadlockException` nas 48h até 06/11. **Armadilha do Blue/Green no segment:** no switchover de 26/10 (Constantinos), os workers nas EC2 legadas continuaram conectados à instância antiga e precisaram de restart. Depois de um switchover, conferir se os workers do ASG reconectaram.

**Alavanca sem código:** cada host do ASG roda o `docker-compose.prod.yml` inteiro: `worker_player_segment_update` com `replicas: 2` e `worker_segment_balance_sqs` com 3. Com 6 hosts são 12 drains. O drain pega um advisory lock por scope (domain, currency, event_class) e pula o scope que já está com outro worker, então drain além do número de scopes ativos só soma scan. Baixar o drain para 1 por host mantém os 18 consumidores da fila de balance e corta metade do scan. Não medi quantos scopes ficam ativos no pico.

**Hotfix PR #843** (`hotfix` branch, celesta-segment; Lucas ganhou push em 06/11): `worker_player_segment_update` `replicas: 2 → 1`. Review 06/11 ~21h UTC:
- Spans `segment.player_segment_update.backlog` (prod-1 = host `datadog-ec2-celesta`): 17–21h com 12 drains, scopes avg 8–9 / max 15, lag avg 66–78 s / max ~100 s, estável; **o maior scope tem ~90% das linhas pendentes** e o lock por scope já o serializa num worker só. Ontem com 6 drains, 63 s (mas entrada estrangulada na SQS). Amostragem fina: 8–16 spans/h.
- **Sem monitor no lag da tabela** (`@oldest_age_seconds`); só há monitor de idade de SQS (21873391, 105331115). Com menos drain, backlog cresce na tabela, invisível à fila, e o scan fica mais caro. Vigiar depois do deploy; monitor é follow-up dos donos.
- Deploy prod-1 (`celesta-rundeck` `deploy_segment.yaml` → `deploy_release.yaml`): `git reset --hard origin/<tag>`, copia `docker-compose.prod.yml` e `docker compose up -d --force-recreate` → `replicas` do arquivo vale no 1º deploy de tag com o commit. `resize_as.sh` lê o desired atual, dobra no roll e restaura: preserva o 6. O roll dobra hosts por uns minutos: não deployar no pico 19–22h.

**Switchover (21:10 UTC, ~2 s sem escrita):** green 8.4.11 db.t4g.xlarge assumiu o nome; a antiga virou `-old1` (read-only). Os consumers reconectaram (6 `ConnectionLost`). **Os drains ficaram presos na `-old1`** com conexão aberta: ~23k erros/min `1290 --read-only` do `player-segment:update`, sem drenar nada, e 11 conexões na antiga. Ninguém reiniciou; saíram sozinhos pelo `--time-limit=3600` e às **21:26** a `-old1` chegou a 0 conexões. Na próxima vez: reiniciar `worker_player_segment_update` logo depois do switchover (Rundeck Commands, filtro `as-segment-worker-i.*`). A prova é conexões na `-old1` = 0 (CloudWatch `DatabaseConnections`) + nenhum erro de read-only.
- Fila failed: 345 mensagens na troca, tratadas pelo Ghislain, 0 desde 22h. O monitor voltou a OK às 21:16; o PD foi resolvido pelo Ghislain às 21:58.
- 07/11: CPU da nova entre 12 e 32% (média horária), idade da balance ~7 s. Com todos os drains de volta, ~50% em 4 vCPU = mesma carga de antes: a troca deu folga, não reduziu o trabalho. #843 segue aberto esperando approve.

**Reabrir se:** idade da mais antiga sair de segundos para minutos **com** CPU colada em ~100%. Aí o banco virou o gargalo, mais worker não ajuda, e é escalar (Randy/SRE).

**Depois, horário comercial:** a query de backlog roda por worker, então a carga no banco escala com o ASG. Candidata a ticket: calcular o backlog uma vez (ou cachear), não em cada worker. E as 3 máquinas novas sem agente do Datadog.
