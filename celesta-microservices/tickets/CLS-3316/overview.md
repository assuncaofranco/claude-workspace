# CLS-3316 — overview
2026-11-17 · 7 sub-tasks

| Sub-task | Repositório | Fonte |
|---|---|---|
| 4743 | promotion | código |
| 4744 | promotion | código (empilhada sobre 4743) |
| 4745 | backoffice | código |
| 4746 | backoffice-front | código |
| 4747 | etl | código |
| 4748 | backoffice | sem branch, sem plano |
| 5130 | scenario | código |

---

## CLS-4743 · celesta-promotion · reasonId on reward configurations and bonuses
**Fonte:** código (`CLS-4743` @ `51a4fa7f6`). OpenAPI regerado da branch e do `origin/master`.

### alteração · POST /api/domain/{domainId}/reward-configuration
**Request**
```json
{
  "reasonId": 3,              // + integer|null, opcional
  "…": "o resto não mudou"
}
```
**Response 200**
```json
{
  "reasonId": 3,              // + integer|null
  "reasonName": "Welcome",    // + string|null, também quando o motivo foi apagado
  "…": "o resto não mudou"
}
```
**Erros novos**
- 400 `reasonId: This reason does not exist.` — motivo de outro domínio, inexistente, ou apagado que não é o atual da configuração
- 400 `reasonId: This value should be positive.` — `reasonId` ≤ 0

**Compatibilidade:** não quebra. Campo opcional novo no request e campos novos na resposta; quem chama hoje (BO) não manda nem lê.

### alteração · PATCH /api/domain/{domainId}/reward-configuration/{id}
**Request**
```json
{
  "reasonId": 3,              // + integer|null; chave ausente mantém, null limpa
  "reason": "welcome",        // ~ passa a ser validado contra as 31 chaves só quando enviado
  "…": "o resto não mudou"
}
```
**Response 200:** `+ reasonId`, `+ reasonName` (como acima).
**Erros novos**
- 400 `reasonId: This reason does not exist.` · 400 `reasonId: This value should be positive.`

**Compatibilidade:** não quebra, e **conserta** um caso: hoje todo edit manda `reason`; depois que o BO parar de mandar, uma configuração com chave fora das 31 daria 400 em todo edit. O `Choice` só roda quando `reason` vem no body.

### alteração · POST /api/domain/{domainId}/player/{playerId}/reward-configuration/{rewardConfigurationId}/offer
**Request**
```json
{
  "reasonId": 3,              // + integer|null, opcional; sem ele, null = bônus sem motivo
  "…": "o resto não mudou"
}
```
**Erros novos**
- 400 `reasonId: This reason does not exist.` — do BO: motivo do domínio e não apagado, ou o da própria configuração mesmo apagado; do scenario: qualquer motivo do domínio, apagado incluído
- 400 `reasonId: This value should be positive.`

**Compatibilidade:** não quebra quem chama hoje (BO, scenario): campo opcional. **Muda o dado gravado:** o bônus passa a ter o próprio motivo; quem não manda `reasonId` continua gerando bônus sem motivo (não herda o da configuração).

### alteração · leituras (só resposta)
`GET /api/domain/{domainId}/reward-configuration/{id}`, `GET …/reward-configurations`, `GET …/bonuses`, `POST …/reward/bonuses/claim`:
```json
{
  "reasonId": 3,              // + integer|null
  "reasonName": "Welcome"     // + string|null
}
```
(na lista de `bonuses` por item; no `claim`, dentro de `rewardConfiguration`). **Compatibilidade:** não quebra, só campos novos.

### Entidade · `reward_configuration`, `bonus`
Migration `Version20261116103914` (`down` desfaz).

| Tabela | Campo | Tipo | Nullable | Default | Mudança |
|---|---|---|---|---|---|
| reward_configuration | reason_id | INT | sim | NULL | + |
| bonus | reason_id | INT | sim | NULL | + |

Índice `reason_id` e FK para `reward_offering_reason(id)` nas duas. Coluna entra por `ALGORITHM=INSTANT`, índice e FK por `INPLACE, LOCK=NONE`: sem reescrever linha nem bloquear escrita.

---

## CLS-4744 · celesta-promotion · seed legacy reasons per brand, backfill reasonId
**Fonte:** código (`CLS-4744` @ `cefeb3768`), **empilhada sobre CLS-4743**: o diff abaixo é contra a ponta do `CLS-4743`. OpenAPI: sem mudança contra o 4743.

### Command · `reward-offering-reason:migrate-legacy <bonusesCreatedUntil>`
- **Dispara:** manual, por quem faz o deploy. Argumento obrigatório: data-hora UTC, no passado (`Y-m-d H:i:s`); bônus criados até ali recebem o motivo da configuração. Opções: `--dry-run` (lista o que semearia, não escreve), `--batch-size` (padrão 1000), `--sleep` (ms entre janelas, padrão 100).
- **O que faz:** (1) por domínio, cria um motivo para cada chave antiga distinta das configurações que ainda não têm `reason_id` (ou reaproveita o motivo de mesmo nome) e liga as configurações; (2) copia o `reason_id` da configuração para os bônus até o corte; (3) imprime, por domínio, quantos têm e quantos não têm motivo.
- **Lote:** 1000 ids de `bonus` por janela (faixa `BETWEEN`, não 1000 linhas lidas). Janelas = (maior id − menor id + 1) ÷ 1000; cada janela roda **2 vezes** (copia e conta), então 2 × janelas statements. **Não medido:** falta o número de bônus em produção.
- **Memória:** o PHP não carrega linhas: cada janela é um `UPDATE … JOIN` no banco e um `GROUP BY domínio` que devolve uma linha por domínio. O que fica na memória é o relatório (domínios × uma linha) e a lista de pares (domínio, chave) a semear, no máximo domínios × 31. Conta com 31 chaves × N domínios; **não medido:** falta N de domínios e o limite do container.
- **Tempo:** ≈ 2 × janelas × (100 ms de pausa + tempo do `UPDATE`). Só a pausa, para 1.000 janelas (1 milhão de ids), dá 2 × 1.000 × 0,1 s ≈ 200 s. **Não medido:** falta o tempo do `UPDATE` por janela.
- **Lock:** `LockFactory`, nome `reward-offering-reason:migrate-legacy`, TTL 300 s renovado a cada janela e a cada par semeado. Segunda execução: `Another run is in progress.` e sai com falha.
- **Idempotente:** sim. Só toca `reason_id IS NULL` (bônus e configuração) e reaproveita motivo de mesmo nome; rodar de novo não duplica nada, só reconta.
- **Se parar no meio:** cada par semeado é uma transação própria, cada janela é um statement próprio. Nada fica pela metade; rodar de novo continua de onde parou. Sai com falha (código ≠ 0) enquanto o relatório mostrar configuração ou bônus sem motivo.

---

## CLS-4745 · celesta-backoffice · pass reasonId on configurations, manual and bulk offers
**Fonte:** código (`CLS-4745` @ `d8b8aaf52`). OpenAPI regerado da branch e do `origin/master`. Esta camada só repassa o que a promotion (4743) aceita.

### alteração · POST /api/gateway/domain/{domainId}/bonus_configuration
### alteração · PUT /api/gateway/domain/{domainId}/bonus_configuration/{id}
### alteração · POST /api/gateway/domain/{domainId}/reward_configuration/gift
### alteração · PUT /api/gateway/domain/{domainId}/reward_configuration/gift/{id}
### alteração · POST /api/gateway/domain/{domainId}/player/{playerId}/bonus_configuration/{id}/offer
**Request**
```json
{
  "reasonId": 3,              // + integer|null, opcional
  "reason": "welcome",        // ~ só é repassado à promotion quando vem no body
  "…": "o resto não mudou"
}
```
**Response 200** (as quatro primeiras; o offer manual não mudou): `+ reasonId` integer|null, `+ reasonName` string|null.
**Erros novos:** 400 `reasonId: This value should be positive.` (validado no próprio BO, `reasonId` ≤ 0) e 400 `reasonId: This reason does not exist.` (repassado da promotion).
**Compatibilidade:** não quebra. Campo opcional; no PUT de configuração, chave ausente mantém o motivo e `null` limpa. Quem chama hoje: BO front. **Atenção:** o PUT do gift ainda recebe `reason` do front antes do 4746, e o BO o ignora.

### alteração · leituras (só resposta)
`GET …/bonus_configuration/{id}`, `PATCH …/bonus_configuration/{id}`, `DELETE …/bonus_configuration/{id}`, `POST …/bonus_configuration/{id}/thumbnail`, `POST …/bonus_configurations`, `GET …/bonuses`: `+ reasonId`, `+ reasonName` (por item nas listas). **Compatibilidade:** não quebra.

### alteração · GET /api/gateway/domain/{domainId}/reward-offering-reasons
Sem mudança de campo. **Quem pode chamar:** antes só quem oferece gift ou atualiza motivos; agora também quem oferece bônus, cria ou edita configuração, e quem edita cenário. **Compatibilidade:** não quebra; só deixa de dar 403 para esses papéis.

### Command · bulk offer de bônus (sem endpoint novo)
**Dispara:** a ação em massa já existente. Muda: para cada item, lê a configuração na promotion (`reasonId`) e manda esse `reasonId` na oferta; **uma chamada de leitura a mais por item**. Lote, memória, lock e idempotência: sem mudança. **Não medido:** falta o tamanho típico de um bulk para a conta das chamadas extras (itens × 1 `GET`).

---

## CLS-4746 · celesta-backoffice-front · reason selects use reward offering reasons
**Fonte:** código (`origin/CLS-4746` @ `2d4ce8968`). Sem OpenAPI (front): contorno tirado do diff das chamadas.

### O que a tela passa a mandar e deixa de mandar
- Oferta manual de bônus e de gift, edição de configuração, criação (wizard) e ação de bônus no cenário: o select de motivo passa a listar `reward-offering-reasons` do domínio e a mandar `reasonId` (inteiro ou `null`), não mais a chave `reason`.
- A lista de configurações do select de bônus **deixa de filtrar** por `filter.reasons`: a barra de busca da lista de reward configurations **não** foi tocada (por isso o 4748 continua bloqueado).
- O edit do gift ainda manda `reason`; o BO o ignora (4745).

**Compatibilidade:** depende de ordem de deploy. Se o front subir antes do 4745, a oferta manual de bônus dá 400 por campo extra (o form do BO não aceita campo desconhecido) e a criação/edição de configuração perde o motivo em silêncio (o form aceita e descarta). Se subir antes do 5130, **todo save de cenário com ação de bônus dá 400** (o scenario recusa campo extra). Ordem segura: 4743 → 4745 + 5130 → 4746.

---

## CLS-4747 · celesta-etl · reward_bonus reason from the bonus's reward offering reason
**Fonte:** código (`CLS-4747` @ `f646b454d`). Sem OpenAPI (Python): só a query do job.

### Job · `promotion.reward_bonus.bigquery_copy_mysql_to_global` (alteração)
- **O que muda:** a coluna `reward_configuration_reason` do BigQuery deixa de ser a chave antiga da configuração (`rc.reason`) e passa a ser o **nome do motivo do bônus** (`REPLACE(ror.name, '\n', '')`), lido por `LEFT JOIN reward_offering_reason ror ON b.reason_id = ror.id`, inclusive motivo apagado. A CTE de bônus passa a ler `bonus.reason_id`.
- **Dispara, lote, lock, idempotência:** sem mudança (o mesmo sync por faixa de id, `limit` existente). O join é por chave primária e `LEFT`: no máximo 1 linha por bônus, o número de linhas não muda.
- **Memória e tempo:** sem mudança de ordem de grandeza; **não medido** o custo do join extra.
- **Compatibilidade:** muda o **valor** para quem lê no BigQuery: bônus sem motivo viram `NULL` (antes carregavam a chave da configuração), e valores novos são nomes, não as 31 chaves. **Quebra o sync se rodar antes da migration do 4743** (coluna `bonus.reason_id` inexistente).

---

## CLS-4748 · celesta-backoffice · remove the legacy reason filter from the bonus-model list
**Fonte:** sem branch, sem plano. Nada a mostrar ainda (só rascunho local, que não é fonte).

---

## CLS-5130 · celesta-scenario · accept an optional reasonId on the bonus action
**Fonte:** código (`CLS-5130` @ `d3fa923e1`). **Sem OpenAPI:** o gerador falha no clone (`Class "Celesta\TaggableBundle\Query\TagEmbedder" not found`, vendor do clone desatualizado). Contorno tirado das anotações e do diff do código.

### alteração · POST /api/scenario e PUT /api/scenario/graph/{scenarioId}
O motivo mora nas `options` do nó de ação `offer_reward`, tanto bônus quanto gift.
**Request (nó da ação, em `nodes[]`)**
```json
{
  "options": {
    "reasonId": 3,            // + integer|null, opcional, no bônus (no gift o campo já existia)
    "…": "o resto não mudou"
  }
}
```
**Erros novos** (400, `Validation errors`, em `nodes.<posição>.options.reasonId`)
- `This value should be positive.` — bônus
- `This value is not a valid reward offering reason.` — bônus e gift: motivo de outro domínio ou inexistente
- `This reward offering reason is deleted.` — bônus e gift: motivo apagado que o cenário ainda não tinha nesse tipo de ação

**Compatibilidade:** não quebra cenário salvo (campo opcional). **Muda no gift:** antes só aceitava motivo não apagado do domínio; agora aceita um apagado **se o cenário já o tinha** numa ação `offer_reward`, para não impedir o save de cenário antigo.

### Command · execução da ação (job do cenário)
**Dispara:** a ação `offer_reward` do cenário, por jogador. Muda: manda `reasonId` ao oferecer o bônus (só se > 0). Se a promotion recusar **só** por `reasonId` (motivo apagado depois do save), a oferta é **pulada** como as outras recusas de nó, sem código de skip. Lote, memória, lock: sem mudança. **Custo novo:** 1 chamada de leitura de motivos à promotion por **save** de cenário (não por jogador), para validar.
