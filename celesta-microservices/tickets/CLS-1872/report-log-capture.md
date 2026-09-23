# CLS-1872 — um critério de aceitação não pode ser cumprido do nosso lado

**O relatório completo está em `~/.claude-secrets/celesta-prod-log-capture-report.md`**, fora de
qualquer repositório. Ele contém a linha de log capturada em produção, o link que fixa o documento no
Datadog, o caminho exato no bucket e o arquivo/linhas do manifesto que criam a captura — material que
não vai para um repositório enquanto a falha estiver aberta.

O que fica aqui é o suficiente para conduzir o épico:

**O código cumpre a AC; a infraestrutura que ele atravessa, não.** O CLS-1872 exige que nenhum valor
de `options` apareça em mensagem de erro ou linha de log. Erros de provedor nunca são ecoados na
resposta — o validator lança mensagem fixa e descarta o texto do provedor. Rodei o fluxo completo
local (criar, atualizar, options rejeitado, provedor inalcançável) e procurei nos logs de aplicação
dos dois serviços um valor-marcador plantado dentro do `options`: zero ocorrências.

**O sidecar nginx registra tudo.** celesta-game grava o corpo inteiro da requisição e os primeiros
1000 bytes do corpo da resposta em toda linha de access log, em toda rota e todo status. Dois
destinos independentes: stdout, coletado pelo agente Datadog, e syslog para o fluentbit, que arquiva
em S3 com retenção de 90 dias. As únicas exclusões são healthcheck, `/`, `/health` e `/open-api.json`.

**Escopo, e os dois fatos estreitam a questão:**

- Só celesta-game e celesta-promotion têm esse `log_format`. O celesta-backoffice registra apenas a
  linha de requisição, sem body nem header — então a exposição do épico é um salto só.
- A captura está na **base do kustomize**, sem overlay que a desligue: vale para os seis ambientes.
  Testar em preprod com credencial real de provedor escreve essa credencial nos logs de preprod.

**Encaminhamento.** Não é "excluir as rotas de game-gateways da captura", é "revisar a captura
inteira", com prioridade acima deste épico — o vazamento já acontece hoje, sem o CLS-1872. Ticket
próprio, dono no DevOps, provável conversa com segurança/DPO pelo dado pessoal envolvido.

**Dependência para o CLS-1872:** não deployar 2978/2979 antes de a captura estar resolvida.
