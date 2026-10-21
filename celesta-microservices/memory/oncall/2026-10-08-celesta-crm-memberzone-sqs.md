# 2026-10-08 — Celesta SQS Messages Visible above 1k, celesta-prod-memberzone.fifo

Alerta P1 às 09:24 local (08:23 UTC). A fila é do **CRM** (memberzone = `crm-active`) e vive na conta quanta-aws `954607206481`, que o Datadog chama de `celesta-legacy`. Entra no console pelo **número da conta**, porque o alias mudou.

**Causa (Marco Gomes, na thread):** um usuário do BO no domínio 53 criou e editou segmentos grandes entre 07:56 e 08:01 UTC. O segmento 85899 casou 961 mil jogadores e foi apagado 6 s depois: todo jogador foi vinculado e desvinculado. O segment emitiu 3.779 mensagens, com 3,36 milhões de operações de vincular e desvincular. O worker do CRM aplica cada mensagem como bulk de 1.000 documentos no Elasticsearch `es-v2-prod-memberzone`, que foi de 12% para **100% de CPU** às 08:00 UTC. Cada mensagem levou 10 a 16 s, e 12 workers drenaram ~1 por segundo. De volta ao normal às ~08:55 UTC.

**O que o console mostrou:** pico de ~2,4 mil mensagens visíveis às 08:00, drenadas até 08:48. Leituras vazias em 0 durante o pico (workers ocupados, não travados). 50 a 85 grupos FIFO em processamento. Entre 08:00 e 08:30 os workers não logaram nada: os `synchronize:kyc` pararam, presos atrás do lote.

**Erros meus no caminho, para não repetir:**
- Supus bloqueio de grupo FIFO porque os logs pareciam ociosos. Os logs só mostram o `synchronize:kyc`, e as leituras vazias em 0 desmentiram.
- Procurei o produtor nos cronjobs e nos health checks do Rundeck às 08:01. Eram uma coincidência: foi ação manual de um usuário do BO. O caminho certo era o CPU do ES e os traces do APM.

**Posição levada à thread:** escalar os workers por CPU não resolve, porque o gargalo é o ES. O conserto de verdade é um guard rail no segment: um segmento apagado logo depois de criado não deveria propagar. O alerta seria mais útil por idade da mensagem mais antiga do que por "mais de 1.000 visíveis".

**Desdobramentos (não são do oncall):** Randy pediu guard rail. Ghislain pediu autoscaling, e o Lucas Azevedo vai revisar o scaling.
