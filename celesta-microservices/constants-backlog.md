# A dívida do teste de constantes

O detalhe Celesta que a skill genérica `ticket-code` referencia sem descrever.

## O que acontece

`ConstantManager::getConstants()` faz reflection sobre **toda** classe sob
`vendor/lancasters/constants/src` e publica todas. Qualquer constante nova aparece na hora na resposta
de `/constants`.

`tests/GatewayBundle/Controller/ConstantControllerTest.php`, no **celesta-backoffice**, afirma esse
payload inteiro contra um array esperado mantido à mão. Ele quebra até a chave nova ser adicionada
lá — mesmo quando o ticket não tem nada a ver com backoffice, e mesmo quando a CI é o primeiro lugar
onde você percebe.

Depois de adicionar qualquer coisa ao `celesta-constants`, atualizar a expectativa desse teste **no
mesmo ticket**.

## Por que a dívida cresce sozinha

Constantes são adicionadas para o serviço que precisa delas — quase nunca o backoffice. Mas é no
backoffice que todas afloram. Ninguém atualiza esse teste até um ticket forçar, então a distância
entre a biblioteca e a expectativa do backoffice cresce em silêncio, e o próximo ticket que mexer em
constantes no backoffice herda o saldo inteiro.

Esperar que a falha inclua constantes de outras pessoas junto com as suas. Pagar isso **não** está
fora de escopo: o teste afirma o payload inteiro, então não há como passar adicionando só o que é seu.

## Duas notas práticas

- Rodar `git diff origin/master...HEAD` **dentro da biblioteca de constantes** para separar as suas
  constantes das que só vieram junto com o master. Adicionar as duas, mas saber qual é qual: as suas
  você é dono, o resto você está só acertando.
- A asserção é `assertEquals`, então ordem de chave não importa. Derivar o valor esperado **da própria
  classe de constante**, nunca do texto do diff da CI — uma constante `null` usada como chave de array
  vira `''`, e copiar a saída da CI esconde isso.
