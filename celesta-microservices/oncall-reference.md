# Oncall — referência Celesta

Lido **uma vez por turno**, por `oncall-shift` e por `oncall`. Tudo de oncall da Celesta mora aqui; o
`context.yaml` não repete.

Destilado da policy de oncall da empresa (2026-10-02). A policy original não é versionada: este repo
sobe para conta pessoal e ela traz remuneração e regra interna.

## Turno

- 1 semana: sexta 09:00 UTC → sexta seguinte 08:59 UTC, ou até fechar o que abriu no turno. Escala no
  PagerDuty.
- Responder e começar a trabalhar em **≤ 15 min**. Sem folga no turno; emergência pessoal → avisar o
  gestor na hora.
- Algo impede de trabalhar (acesso, equipamento) → avisar VPoE ou CTO.

## Escalonamento

| Tier | Quem | Sobe quando |
|---|---|---|
| 0 | TL do componente | só horário comercial, alertas do componente dele |
| 1 | oncall | sem ack em **30 min** |
| 2 | VPoE | sem resolver em **60 min** |
| 3 | CTO | — |

Manual: escalar para quem é dono do componente. Não respondeu (não está de oncall), subir de tier sem
hesitar. O texto de escalonamento segue a skill `oncall`, saída ESCALAR.

## Canais

| Canal | Para quê | Ambiente → perfil AWS / contexto kube |
|---|---|---|
| `#celesta-alarms-prod-1` | eventos do PagerDuty | prod-1 → `celesta-prod-1` / `celesta-prod-1` |
| `#celesta-alarms-prod-2` | eventos do PagerDuty, sportsbook | prod-2 → `celesta-anj-prod-1` / `celesta-anj-prod-1`. Não existe nada chamado `celesta-prod-2`: o canal diz prod-2, a role diz anj |
| `#celesta-oncall` | falar com todo o oncall; handoff vai aqui | — |
| `#celesta-support-winspire` | pedido de negócio | — |
| `#celesta-brand` | pedido de marca | — |
| `#celesta-statuspage-notifications` | status page | — |
| `#sre-b2b-celesta` | não está na policy. Anúncio do time de SRE e relatório diário do Datadog (5xx por serviço). Não chega alarme | na triagem, procurar aqui mudança de infra recente que explique o alerta, antes de suspeitar de código |

Jobs agendados: Rundeck (`https://rundeck.octopoprod.com/`) e Jenkins.

## Gravidade por serviço

| Régua | Serviços |
|---|---|
| dinheiro | celesta-payment, celesta-wallet, celesta-sb-wallet |
| jogador | celesta-gateway, celesta-game, celesta-promotion, celesta-auth |
| quase nunca urgente | celesta-statistics, celesta-segment, celesta-activity |

## Checklist de início

| # | Item | Quem | Confirmação |
|---|---|---|---|
| 1 | Laptop, celular e carregadores à mão; internet estável | Lucas | ok verbal |
| 2 | Notificação de início de turno do PagerDuty recebida | Lucas | ok verbal |
| 3 | App do PagerDuty: alta urgência fura o "não perturbe" do celular | Lucas | ok verbal |
| 4 | Slack no celular: notificação de todas as mensagens em `#celesta-alarms-prod-1` e `#celesta-oncall`, todos os canais da tabela acima entrados, horário de "não perturbe" do Slack desligado | Lucas | ok verbal |
| 5 | VPN: NordLayer no gateway privado **Celesta Network**, não num país de "Shared gateways" | Lucas | eu: `pgrep -fl 'NordLayer.app/.*/ovpn'` (OpenVPN) **ou** `scutil --nc list \| grep '(Connected).*NordLayer'` (NordLynx); o gateway só ele vê |
| 6 | MFA: `awsmfa` (código ao vivo, só ele roda) | Lucas | eu: `aws sts get-caller-identity --profile <perfil>` para `celesta-prod-1` e `celesta-anj-prod-1` |
| 7 | Pods de prod visíveis, nos dois contextos | eu | `kubectl --context <contexto> get pods -A --no-headers \| awk '{print $4}' \| sort \| uniq -c` |
| 8 | Freelens abre `celesta-prod-1` e `celesta-anj-prod-1` | Lucas | ok verbal |
| 9 | 1Password: cofre on-call compartilhado visível | Lucas | ok verbal |
| 10 | Login em Rundeck e Jenkins | Lucas | ok verbal |
| 11 | App do Datadog no celular logado | Lucas | ok verbal |
| 12 | Conectores do Claude: Datadog, PagerDuty, Slack, AWS MCP | Lucas, no claude.ai | eu: listar o que a sessão alcança |

Item 5, por quê: o `scutil` só conhece o perfil NordLynx. Conectado em OpenVPN ele diz
`Disconnected` com o túnel de pé (2026-10-02). E `grep -i connected` casa com "Disconnected".

Primeira vez na vida (não por turno): instalar e logar Datadog, AWS, Slack, PagerDuty e 1Password no
celular e configurar a notificação do PagerDuty.

**Gap conhecido, não bloqueia:** a fila `segment-balance.fifo` vive na conta `954607206481`
(quanta-aws), que nenhum perfil alcança. Só pelo console, entrando com o **número da conta** e não com o alias: o alias `quanta-aws` mudou em 2026-10-08, e com ele o login dá "authentication failed" mesmo com a senha certa. O Datadog chama essa conta de `celesta-legacy` e tem as métricas `aws.sqs.*` dela, então é por ele. A fila `celesta-prod-memberzone.fifo` (do CRM) também mora lá.

## Checklist de fim

1. Todo alerta e incidente do PagerDuty fechado.
2. Notificação de fim de turno do PagerDuty recebida.
3. Handoff postado em `#celesta-oncall`.
4. Notificações do celular de volta ao normal.

## Incidentes conhecidos

Casar o alerta aqui **antes** de abrir arquivo. Arquivos em `memory/oncall/`.

| Monitor / sinal | Balde | Saída | Arquivo |
|---|---|---|---|
| `SQS Messages Visible above 1k`, `segment-balance.fifo` | spike de fila | reportar; drena sozinho | `2026-08-29-celesta-segment.md` |
| healthcheck Dagster 089, sub_balance de bônus sem bonus no promotion | perda no sync forward | reportar; resync em horário comercial | `2026-09-01-celesta-wallet-promotion.md` |
| `Celesta Game Go Less than 10 hits/sec` → NO DATA | dependência externa (Quanta `gamelauncher/status`) | reportar à Quanta | `2026-09-04-celesta-game-go.md` |
| `Celesta ETL BI Latency is above 20 Minutes`, `reward_bonus` / `segment_player` | ruído conhecido; os dois recarregam a tabela inteira. segment_player bate no limite de 1140s em parte das execuções (intermitente, ver a UI do Dagster) (também dispara "error rate breached 3.0"); fix do reward_bonus no CLS-3113 | reportar; dispara toda noite até o CLS-3113 | `2026-10-02-celesta-etl.md` |
| `Celesta Rundeck Error on Job`, `terminate_long-running_mongodb_operations` | ruído; job roda a cada minuto, monitor soma 6h | conferir no Rundeck se foi isolada; reportar | `2026-10-05-celesta-rundeck.md` |
| `SQS Messages Visible above 1k`, `celesta-prod-memberzone.fifo` (CRM) | spike de fila; segmento gigante no BO → bulk no ES do CRM a 100% de CPU | reportar; drena sozinho. Olhar o CPU do ES `es-v2-prod-memberzone` antes dos workers | `2026-10-08-celesta-crm-memberzone-sqs.md` |
| `Celesta Game Command Job above 1.0 Errors`, `game:big-winner`, `setFirstName ... null given` | contrato do CRM: nome opcional no cadastro não-ANJ (CLS-1837), game exige string | reportar; resolve sozinho quando o jogador completa o cadastro | `2026-10-08-celesta-game-big-winner.md` |
| Error Tracking `celesta-backoffice` `log_count`, 500 de `activity /user-activities/aggregate` | lentidão conhecida: aggregate do activity passa de ~20 s e dá 500; issue desde v1.1331 | reportar; candidato a ticket na query de count do activity | `2026-10-13-celesta-backoffice-logs-count.md` |
| `Game-Go TG ELB above 120ms` / `Game TG ELB above 225ms` / PD `Game Go latency above 95ms` | PreferClose (CEL-9484) concentra o tráfego da 1a em 2 pods da wallet, e o descheduler `LowNodeUtilization` despeja esses pods a cada 3 min; lento só numa AZ, em loop | corrigir: suspender o descheduler via commit no celesta-argocd. Checar `target_response_time.p50 by {availabilityzone}` e `service:descheduler "Evicted pod"` | `2026-10-17-celesta-game-go.md` |
| `Big Query scheduled query failed (Celesta)` (P4 no DD, chega P1 no PD) | dependência externa; `status:unavailable` = transitório do GCP. Erro, SQL e destino ficam no console: BigQuery → Scheduled queries (Lucas tem acesso desde 20/10) | reportar; conferir a próxima execução horária. `6aad1f51` = tabela de bônus, a execução seguinte cobre (sem backfill, Ivan 20/10) | `2026-10-19-celesta-bigquery.md` |
| `Celesta Scenario RDS below 10% Freeable Memory` | performance_schema crescendo por IP de cliente (cron a cada minuto = pod novo = IP novo); blue/green só reseta, volta em ~9 dias. Expedite CLS-3377 | reportar; vigiar `SwapUsage` e latência | `2026-10-03-celesta-scenario-rds.md` |

Padrões de calendário e fornecedor:
- **Dia 29 do mês** → spike na fila do segment (maio e agosto). Causa em aberto.
- **Quanta** caiu duas vezes, em horários diferentes. Fornecedor instável, não padrão de horário.
