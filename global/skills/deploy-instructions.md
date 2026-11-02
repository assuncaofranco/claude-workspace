---
description: Write a ticket's deployment instructions (order, why, what each intermediate state does, rollback, migrations, config) for whoever deploys it, after review and before preprod.
argument-hint: <TICKET>
---

# deploy-instructions

Passo 14 do ticket. Escreve as instruções de deploy de `$ARGUMENTS` para **quem faz o deploy**, que não é
o Lucas e não leu nada da conversa.

## Por que existe

O Lucas não faz o deploy. Ordem errada entre dois serviços quebra produção sem que o código de nenhum
dos dois esteja errado, e quem aperta o botão só sabe a ordem se ela estiver escrita. O Lucas pediu o
passo depois de admitir que às vezes esquecia (CLS-1546, 2026-10-07): ali, o game subindo antes do
backoffice derrubaria a edição de max bet no BO com 400.

Escrever "não há ordem" também é instrução. Silêncio não é.

## Como derivar — da chamada, não da intuição

1. **Listar as entregas:** cada PR de serviço, biblioteca (constants, job-library, com a tag que
   precisa existir), automação de QA (proteus), front, mudança de infra ou de config.
2. **Para cada contrato que o ticket muda**, achar quem chama quem: rota, parâmetro, payload, fila,
   job. Buscar os chamadores em todos os repositórios, não só nos do ticket.
3. **Para cada par, os dois estados intermediários:** chamador novo com chamado velho, e chamador
   velho com chamado novo. Para cada um, dizer o que acontece de fato (erro? qual status? dado
   perdido? nada?). A ordem é a que só passa por estados inofensivos. Se as duas forem inofensivas,
   dizer que a ordem é recomendada, não obrigatória.
4. **Rollback:** repetir o raciocínio voltando um de cada vez. Em geral é a ordem inversa, mas
   verificar: há casos em que um lado volta sozinho sem dano.
5. **O que não é código:** migration (roda sozinha? reversível?), variável de ambiente, fila nova,
   permissão de IAM, feature flag, tag de biblioteca que precisa existir antes do merge.
6. **O que observar depois** de cada deploy, se houver algo concreto a olhar.

Cada afirmação aponta o arquivo ou o comando que a sustenta, como no resto do fluxo.

O raciocínio acima é para **decidir** a ordem; quase nada dele vai para o texto.

## O que se escreve — preguiçoso

Lista de PRs na ordem, uma linha cada, e o rollback na ordem inversa. Nada mais, a não ser um passo
que **não** é deploy de PR (script a rodar, espera por outro time, config).

Nunca: detalhe de migration, "right before step 2", o que acontece na janela, "do not run the
migration down" (deploy e rollback rodam `up` e `down` sozinhos), checagem de banco depois.

**Por quê:** o Lucas cortou a primeira versão do CLS-3282-CLS-4163 (2026-11-02) — explicação em
instrução de deploy é coisa de IA e fica patética; quem aperta o botão lê a ordem, não o porquê.

**Onde a atenção vai de fato:** quando o código e o schema precisam mudar em momentos diferentes
(entidade para de usar a coluna antes de ela sumir, por exemplo), isso vira **dois PRs** e duas
linhas da lista. É o deploy que garante a ordem, não o texto. Migration só aditiva cabe no mesmo PR.

## Onde vai

- **Campos do ticket** quando o tracker tem (na Celesta: Deployment instructions, Rollback
  instructions; Release note só para release de biblioteca, como `job-library: removed X`). É o que
  quem faz o deploy lê de fato.
- **A mesma lista** na seção de post deployment da descrição de **cada** PR envolvido.
- **Pasta do ticket** do overlay, `deployment-instructions.md`, com o porquê de cada passo — o
  raciocínio fica do nosso lado, não no ticket.

## Próximo

Passo 15: perguntar se testamos em preprod (`preprod-test`).
