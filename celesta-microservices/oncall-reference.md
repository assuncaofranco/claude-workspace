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
(quanta-aws), que nenhum perfil alcança. Só pelo console.

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

Padrões de calendário e fornecedor:
- **Dia 29 do mês** → spike na fila do segment (maio e agosto). Causa em aberto.
- **Quanta** caiu duas vezes, em horários diferentes. Fornecedor instável, não padrão de horário.
