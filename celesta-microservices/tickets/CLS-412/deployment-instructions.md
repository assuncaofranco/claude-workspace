# CLS-412 — Deployment instructions (lado do time, 2026-10-19)

Cobre **só os nossos quatro PRs**: os do Lucas, o do Bohdan e o do Rasoul. O épico tem mais entregas
(celesta-scenario, celesta-constants, celesta-job-library, e a doc do backoffice) que são de outras
pessoas e entram depois — ver "O resto do épico" no fim.

A pergunta não é quando a feature fica pronta, é **em que ordem o deploy pode acontecer sem derrubar
nada**. Todo estado intermediário tem que ser inofensivo.

---

## As entregas

| # | Serviço | Branch | Sub-task | Autor | O que muda |
|---|---|---|---|---|---|
| 1 | celesta-promotion | `CLS-412-CLS-2923` | CLS-2923 | Lucas | `bonus`: colunas `source_scenario_id` e `idempotency_key`, `sourceUserId` deixa de ser obrigatório, a lista passa a devolver as duas origens |
| 2 | celesta-promotion | `CLS-412-CLS-3230` | CLS-3230 | Bohdan | `gift`: `source_user_id` passa a aceitar nulo, colunas `source_scenario_id` e `idempotency_key`, validação de uma origem só |
| 3 | celesta-backoffice | `CLS-412-CLS-2923` | CLS-2923 | Lucas | lista de bónus repassa `sourceUserId` e `sourceScenarioId` |
| 4 | celesta-backoffice | `CLS-412-CLS-3230` | CLS-3230 | Rasoul | lista de gifts repassa `sourceScenarioId` |

**A sub-task não identifica o deploy sozinha**: CLS-2923 e CLS-3230 têm cada uma duas entregas, uma em
cada serviço, com a mesma branch. O que identifica é o par **serviço + branch**, que é como as
instruções do CLS-1788 já estão escritas.

Fora da lista: **celesta-qaa-proteus**, branch `CLS-412-CLS-2923`, não é deploy. É a automação de QA;
merge quando quiserem, não vai para ambiente nenhum.

---

## Ordem

```
Deploy celesta-promotion  using branch CLS-412-CLS-2923   ─┐
Deploy celesta-promotion  using branch CLS-412-CLS-3230   ─┘  entre si, qualquer ordem
        ↓
Deploy celesta-backoffice using branch CLS-412-CLS-2923   ─┐
Deploy celesta-backoffice using branch CLS-412-CLS-3230   ─┘  entre si, qualquer ordem
```

**Regra curta: promotion antes de backoffice.**

### Por que promotion primeiro, e por que não é obrigatório

Os dois PRs de backoffice só leem campos. O normalizer deles faz
`$row['sourceScenarioId'] ?? null` (`GatewayBundle/Normalizer/Promotion/BonusNormalizer.php` e
`GiftNormalizer.php`), então os dois estados intermediários são inofensivos:

| Estado | O que acontece |
|---|---|
| backoffice novo, promotion velho | o campo não vem, o `?? null` devolve nulo, a coluna de origem aparece vazia |
| promotion novo, backoffice velho | o campo vem e o whitelist do normalizer descarta, exatamente como hoje |

Nenhum dos dois dá erro. Logo a ordem é **recomendada, não obrigatória**: promotion primeiro só para
que a origem já tenha valor no instante em que o backoffice passa a mostrá-la. Se o deploy sair
trocado, ninguém quebra — a coluna fica vazia até o promotion subir.

### Por que as duas entregas de promotion são independentes

A do CLS-2923 mexe na tabela `bonus`, a do CLS-3230 na `gift`. Não há chamada entre eles e as migrations tocam
tabelas diferentes. A única colisão que havia era de **nome de arquivo** — as duas nasceram com
`Version20261019120000` — e já foi resolvida movendo a do CLS-2923 para `Version20261019143000`,
depois das duas do CLS-3230 (`...120000` e `...120100`).

---

## Migrations

Quatro, todas online, nenhuma precisa de janela:

| Migration | PR | O que faz |
|---|---|---|
| `Version20261019143000` | CLS-2923 | `bonus` ganha `idempotency_key` e `source_scenario_id` (`ALGORITHM=INSTANT`) e o índice único do trio (`INPLACE, LOCK=NONE`) |
| `Version20261019120000` | CLS-3230 | `gift.source_user_id` passa a aceitar nulo (`INPLACE, LOCK=NONE`) |
| `Version20261019120100` | CLS-3230 | `gift` ganha `source_scenario_id`, `idempotency_key` e o índice único |

Rodam sozinhas no deploy do serviço. Não há variável de ambiente nova, fila nova, permissão nova nem
feature flag.

**A flag `move_bonus_to_promotion` não existe mais** — foi removida do promotion em
CLS-2847-CLS-2852, antes destes PRs. Nada neste épico depende dela.

---

## Rollback

Ordem inversa: backoffice primeiro, promotion depois.

Os dois de backoffice voltam sozinhos, sem dano: param de repassar dois campos.

**O CLS-3230 tem um caminho sem volta, e é o único ponto perigoso do épico.** O `down()` dele faz
`ALTER TABLE gift MODIFY source_user_id INT NOT NULL`. A partir do momento em que um cenário criar o
primeiro gift sem utilizador de backoffice, existe linha com `NULL` nessa coluna e esse `ALTER`
**falha**. Depois disso o rollback do CLS-3230 exige decidir o que fazer com essas linhas — não é um
`down()` automático.

Enquanto o celesta-scenario não estiver em produção, nenhum gift nasce sem utilizador e o rollback é
limpo. Ou seja: a janela segura de rollback do CLS-3230 fecha quando o scenario subir.

O CLS-2923 não tem esse problema: o `down()` dele só apaga colunas que ninguém mais lê.

---

## O que observar depois

- **Depois do promotion:** `SELECT COUNT(*) FROM bonus WHERE source_scenario_id IS NOT NULL` deve ser
  zero até o scenario subir. Se não for, alguém está a chamar o endpoint com o campo antes da hora.
- **Depois do backoffice:** abrir a lista de bónus de um jogador e confirmar que as duas colunas de
  origem vêm no payload, mesmo que vazias. Se não vierem, o deploy do backoffice não pegou.

---

## O resto do épico, que não é nosso

Entra **depois** dos quatro acima, e tem ordem própria:

1. `celesta-constants`, branch `CLS-412-CLS-2922` (Pedro) — precisa de tag publicada antes do que a consome
2. `celesta-job-library`, branch `CLS-412-CLS-2935` (Pedro) — idem
3. `celesta-scenario`, branches `CLS-2924` (Damian) e `CLS-412-CLS-2925` (Pedro) — é quem chama o promotion
4. `celesta-backoffice`, branch `CLS-2926` (Damian) — documentação da action

O scenario **tem que ser o último**: ele é o único caller novo do endpoint de offer e do de gift, e
depende das duas bibliotecas e dos dois PRs de promotion já estarem em produção. Subir o scenario
antes do promotion dá 400 em todo jogador alvo, porque `sourceScenarioId` ainda não existe no corpo
aceite.
