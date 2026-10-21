# Datadog — referência Celesta

Onde procurar o quê. Serve para ticket ("isso ainda é usado?"), oncall e consulta.
Levantado em 2026-10-14, no CLS-2485.

## Acesso

- Org única, site **`datadoghq.eu`**. Os dois conectores do claude.ai ("Datadog" e "Datadog (2)")
  apontam para a **mesma org**. O (2) usa endpoint descontinuado; usar o primeiro.
- Somente leitura. O conector precisa ser autorizado **no Claude Code também**, não só no browser
  (`/mcp`).

## Logs × traces — a armadilha

| Pergunta | Onde | Por quê |
|---|---|---|
| Um command rodou? Quantas vezes? | **APM**: `operation_name:symfony.command resource_name:<nome>` | em prod o canal `command` do monolog só grava `error`; execução bem sucedida não gera log |
| Algo do **prod-2** (Sportsbook) | **APM** | logs do prod-2 **não chegam** à org; spans chegam |
| Mensagem de erro, stack trace | logs | |
| Volume de endpoint, latência | APM | |

Logs em prod passam por `fingers_crossed` com `action_level: error`: `info` só aparece se a mesma
request teve erro. **Ausência de log não é ausência de execução.** Antes de concluir "nunca roda",
rodar um **controle positivo** (algo que sabidamente roda) na mesma query.

## Nomes

- Service: `celesta-<ms>` (principal) e `<ms>` (legado, volume baixo). Filtrar `service:*<ms>*`.
- Env: `prod-1`, `prod-2`, `staging-1`, `preprod-N`, e às vezes a tag dupla `preprod,preprod-N`.
- Command no APM: dois spans por execução (`symfony.command` e `symfony.console.command.run`, mesmo
  `resource_name`). Contar só um.

## Retenção observada

- Spans: ~30 dias.
- Logs: consultar com `storage_tier: flex_and_indexes` para pegar o Flex.

## Economia de token

Sempre agregar primeiro (`aggregate_spans`, `analyze_datadog_logs` com `GROUP BY`) e só listar
eventos individuais quando a contagem for > 0.
