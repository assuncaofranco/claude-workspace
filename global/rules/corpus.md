# Como mudar estas regras

Carregado quando o Lucas pede para mudar como eu trabalho. Vale **antes** de editar qualquer arquivo
de `rules/`, `router.md` ou uma skill.

## Uma definição, um lugar

Toda regra existe **uma vez**. Um fluxo que precisa dela **referencia** o arquivo; não reescreve o
conteúdo. Se você se pegar explicando a mesma regra em dois arquivos, um dos dois está errado.

O teste: mudar a regra deve ser editar **um** arquivo.

## Contradição é para ser mostrada, não contornada

Quando uma instrução nova contradiz uma regra existente:

1. **Abrir o arquivo da regra** e ler o que já está lá, incluindo as exceções.
2. **Mostrar o conflito ao Lucas**, citando as duas formulações.
3. **Perguntar qual das duas saídas:**
   - *substituir* — a regra antiga estava errada ou ficou obsoleta, e sai;
   - *exceção nomeada* — as duas valem, e a nova entra **no mesmo arquivo** com a condição que a
     distingue da regra geral.
4. Só então editar.

**O que nunca fazer:** escrever a instrução nova em outro arquivo porque lá não há conflito aparente.
É assim que o corpo de regras fica inconsistente sem ninguém perceber — cada arquivo individualmente
coerente, o conjunto não.

**Isso já aconteceu.** A regra "não consertar fora do escopo do ticket" viveu meses em um arquivo
enquanto a sua única exceção (o teste de constantes, que exige reconciliar o payload inteiro) foi
escrita em outro, num ticket diferente. Quem lesse só o primeiro tinha a resposta errada naquele caso.
Hoje as duas estão em `scope.md`, juntas — e é por isso que uma exceção mora **dentro** do arquivo da
regra que ela excepciona, nunca ao lado.

## Onde cada coisa entra

| O que é | Onde vai |
|---|---|
| Regra de como trabalhar, vale em qualquer empresa | `rules/<tema>.md` |
| Qual arquivo carregar em qual situação | `router.md` |
| Sequência de passos de um fluxo | a skill correspondente |
| Nome de serviço, container, caminho, credencial | overlay do projeto, nunca aqui |
| O que aconteceu num ticket | `memory/tasks/<ticket>/` |

Se não couber em nenhuma linha, a dúvida é legítima — perguntar em vez de escolher a mais próxima.

## O porquê fica junto

Cada regra carrega o caso real que a originou. Não é histórico: é o que permite reconhecer quando ela
se aplica e quando não. Uma regra sem o porquê é aplicada literalmente nos casos errados — e é
justamente o que produz a contradição que esta página existe para evitar.
