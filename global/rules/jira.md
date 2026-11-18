# Jira: o que escrevo e o que espera pedido

Nada nosso vai para o Jira sem o Lucas pedir aquela escrita com todas as letras, naquele momento.
Vale para comentário e link entre issues, e para qualquer escrita que não esteja na exceção abaixo.
"Posta", "você confere e posta" ou uma regra de skill não contam como pedido.

## Exceção nomeada: o board e o que o próprio SDD escreve

Vão **sem perguntar**:

- as transições da tabela "O que conferir em cada parada do SDD" em `skills/ticket-story.md`
  (sub-task: Planned, In Progress, To review; pai: Implementing), cada uma no momento que a tabela
  diz. Implemented continua só depois do review humano, como está lá;
- o que uma fase do SDD escreve por conta própria: o label da fase (`sdd-plan`, …), o comentário
  de custo e, no `sdd-release`, o link do manifesto no campo Deployment instructions do pai, só
  quando o campo está vazio (decisão do Lucas, 2026-11-16, CLS-1214). Vale também quando a fase
  roda num agente nosso ou fecha o passo que uma sessão anterior deixou pela metade.

Continua pedindo: **comentário nosso** (pergunta ao PO ou ao TL, achado de review, aviso) e
**link** entre issues.

**Por quê da exceção:** decisão do Lucas, 2026-11-16 (CLS-1214). O board e as marcas do SDD fazem
parte do fluxo combinado, e perguntar a cada parada só atrasa. O que suja o ticket é texto nosso.

## Para onde vai o que não vai para o Jira

Num review, todo comentário vai para o autor no PR do GitHub: achado de código inline; achado sobre
plano, spec ou AC do pai no comentário global do PR. Pergunta de produto vai ao autor, pedindo que
ele confira com o PO. Se não cabe como comentário ao autor, não é postado.

**Por quê:** nas palavras dele, comentário no Jira "suja muito e às vezes nem seria preciso".
Aconteceu duas vezes:

- no review do CLS-4067 (2026-10-28) postei no Jira as perguntas de plano e AC. Ele apagou e levou
  para o comentário global do PR;
- no CLS-3916 (2026-11-16) li "você confere e posta" como licença para o Jira. Postei perguntas ao
  PO e ao TL como comentário no CLS-3916 e no CLS-3316 e criei um link Blocks. Resposta dele: "Nada
  vai para o Jira sem eu pedir com todas as letras, nem comentário."

## Como aplicar

Antes de qualquer ferramenta de escrita no Jira: se a escrita está na exceção, segue. Se não está,
procurar na mensagem dele o pedido daquela escrita; sem pedido, mostrar o texto ou a ação e
perguntar onde vai. O brief de um agente diz o mesmo: transições e marcas do SDD liberadas,
comentário nosso e link proibidos.
