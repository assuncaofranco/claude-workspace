---
name: cls2594-cls3055-gift-review
description: "Review do PR 531 (Gift endpoints, celesta-promotion) em 2026-09-23 - onde mora o KPI de generosity e os três buracos do épico"
metadata: 
  node_type: memory
  type: project
  originSessionId: ea5a7dcd-e1a8-4b25-9adb-ba700f38f55d
  modified: 2026-09-23T14:42:57.742Z
---

# CLS-2594 (Physical gift reward type) / CLS-3055 (endpoints)

**O que é um gift:** anotação contábil de um presente entregue **fora** do sistema (VIP: ingresso,
jantar, eletrônico). Não credita carteira, não notifica, não tem estado pendente. O endpoint só
**lê** o Wallet para saber em que moedas o jogador tem carteira. `status = claimed` é palavra
emprestada do vocabulário de bônus para o KPI poder se chamar "Claimed gifts amount".

Não existe gift configuration: o BO digita nome, valor, moeda e descrição a cada oferta. A primeira
versão (21/09) encaixou gift debaixo de reward configuration e ficou verde; o TL desfez em 22/09.

## Onde mora o KPI de generosity (isto não está em nenhum repo do promotion)

`generosity` é coluna `NUMERIC(16,2)` em `master_player_report`, no **celesta-statistics**
(`src/Migrations/Version20221118094255.php`). Quem preenche é pipeline de BI — subtask **CLS-3044**.
O backoffice só lê, por moeda e por período:
`PlayerStatisticsKpiManager::getStatisticsData()` → `statisticsClient->getKpiData($playerId, $currency, [from, to])`.

Consequência: o `/gifts/aggregate` do promotion **não** está no caminho do KPI. Ele conta linha para
paginar lista no BO, e não soma `amount`.

## Três buracos do épico, nenhum deles do PR 531

1. **Ninguém é dono de tornar `gift` visível ao BI.** Nem o 3054, nem o 3055, nem o 3044 dizem quem
   ensina o pipeline a enxergar a tabela nova.
2. **Moeda.** A fórmula soma `Σ bonuses + gift value`, mas o gift é digitado em qualquer moeda em que
   o jogador tenha carteira e o pai diz "no FX conversion at offer time". Jogador multi-moeda sai
   errado a menos que o BI converta. Ninguém diz quem converte.
3. **Data.** `gifted_at` foi cortado em 22/09, então a única data é `created_at`. Presente entregue em
   dezembro e digitado em janeiro entra no período de janeiro. O CLS-2957 não menciona data nenhuma.

## Estado do review (2026-09-23)

PR 531 e PR 530 abertos, os dois com base em master; o 531 carrega o commit do 530. Bloqueado pelo
PR 594 do celesta-constants (aprovado, não mergeado): o composer aponta para `dev-CLS-2594-CLS-3054`
e o plano manda trocar para `^1.336` depois do auto-tag.

Postei 4 comentários inline (voz de `global/rules/writing.md`): `description` virando `''` em vez
de null, quatro filtros do spec sem cenário nenhum, o mock do Wallet lançando 404 onde o real devolve
`200 []`, e uma sugestão não bloqueante sobre o plano colar o código final.

**O PR em si está limpo** — não é o padrão "IA criou classe demais". Cada classe nova tem contraparte
1:1 em Bonus ou RewardConfiguration, zero comentário explicativo, `bcadd($x,'0',2)` copiado de
`RewardOfferService:192`, `WalletServiceTest` estendido em vez de duplicado.
