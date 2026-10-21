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

## Onde vai

- **Arquivo completo** na pasta do ticket do overlay do projeto, `deployment-instructions.md`, com o
  porquê de cada passo. Modelo: `celesta-microservices/tickets/CLS-1872/deployment-instructions.md`.
- **Bloco curto em inglês** na seção de post deployment da descrição de **cada** PR envolvido: a
  ordem, a regra de rollback e o que não é código. É o que quem faz o deploy lê de fato.

## Próximo

Passo 15: perguntar se testamos em preprod (`preprod-test`).
