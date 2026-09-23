---
name: feedback-narrate-commands
description: "Sempre mostrar o comando junto da explicação do que foi feito, um por linha"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-16T06:17:17.101Z
---

Toda vez que eu rodar um comando, explicar o que fiz mostrando o comando junto,
no formato "o que foi feito `<comando>`" — uma linha por comando, na ordem em
que rodaram.

Exemplo do formato que ele pediu:
  verifiquei se temos acesso `gh auth status`
  entrei na pasta dos acessos `cd ...`

**Why:** ele não é devops (ainda) e precisa enxergar o mecanismo, não só a
conclusão. Sem o comando ao lado, a resposta é uma afirmação que ele não pode
verificar nem repetir sozinho.

**How to apply:** vale inclusive quando vários comandos vão numa só chamada de
ferramenta — listar cada um na resposta, não só o resumo. Não substitui
[[feedback-explanation-length]]: continua sendo conclusão primeiro, poucas
linhas. Relacionado a [[feedback-explanation-method]], que já pede nunca afirmar
sem um comando atrás.
