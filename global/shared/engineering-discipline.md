# Lições de review que atravessam projeto

Erros pegos por um revisor humano ou automático numa PR, que valem para qualquer lugar. Um item por
lição, com o **porquê** — não narrativa.

O que é específico de um stack ou de uma empresa (thresholds de linter, quais bibliotecas
compartilhadas existem, nomes de tabela) fica no arquivo de padrões daquele projeto, não aqui.

Critério para um item entrar: **a lição sobrevive a trocar de empresa.** Se ela só faz sentido com
o nome de um serviço específico, ela pertence ao arquivo do projeto.

---

## Contrato e acoplamento

**Remover um `throw` de um serviço compartilhado muda o contrato de todos os consumidores, não só do
que o ticket trata.** Aquele throw era um validador implícito. Um caso real: remover o throw de
"moeda não encontrada" de um getter transformou um 404 limpo (o chamador capturava a exceção) num 400
cuja mensagem interpolava `null` e saía como texto vazio. Procurar os consumidores **do método cujo
contrato você relaxou**, não só os usos do campo que você mudou.

**Sondar clientes heterogêneos com `method_exists` para um nome "bem conhecido" pula em silêncio
todos os que o nomearam diferente.** Num caso real, 4 de 14. Derivar a chamada por tipo a partir do
consumidor que de fato a usa, com um `match` no tipo — e testar **um tipo por ramo** da sondagem, não
só o ramo conveniente.

**Constante em vez de literal, quando um `match` seleciona algo que uma classe de constantes já
define.** Um literal que diverge cai no `default =>` — e num caso real isso teria aplicado
silenciosamente a **permissão errada**, em vez de dar erro.

**Mas: antes de "consertar" um braço `default =>` para lançar exceção, verificar se ele roda antes ou
depois do portão de permissão.** Num lookup de camada de serviço, alcançado *depois* do portão,
`default => throw` é correto. Num `match` que *calcula* a permissão a passar para a verificação de
acesso, ele roda **antes** — e uma exceção genérica não é a exceção de acesso negado, então o
listener de segurança do framework nunca a vê e ela vira 500 em vez do 403 normal. Mesma forma de
`match`, resposta correta oposta.

## Entrada do usuário

**Desestruturar `explode()` sobre entrada do usuário é um 500 esperando acontecer.**
`[$a, $b] = explode(':', $input, 2)` emite "Undefined array key 1" quando o separador não veio — e um
projeto que converte warning em exceção transforma isso em erro 500. Usar
`$parts = explode(...); $b = $parts[1] ?? null;` para qualquer valor vindo de requisição.

**"Chave presente" e "valor informado" não são a mesma coisa.** Um saco de parâmetros costuma
implementar `has()` como `array_key_exists`, então um `null` de JSON conta como presente. Para exigir
valor, testar o valor. E nunca confiar num transformador de dados para saber "foi enviado?": a
submissão do formulário converte `false` em `null` antes do transformador rodar, então `false` e
ausente já chegam indistinguíveis lá.

**Desvincular um formulário da sua entidade desliga toda validação de nível de entidade** — incluindo
unicidade. O índice único do banco então aflora como 500 com a mensagem crua do driver, que uma
camada acima pode reetiquetar como 400 e repassar o corpo. Ao desvincular, reimplementar as
restrições que você ainda precisa, ou capturar a violação de unicidade num erro de campo.

## Migrations e cache

**Um `skipIf` no topo de uma migration pula *todo* o resto dela**, inclusive comandos não
relacionados mais abaixo. Guardar cada bloco de DDL na sua própria condição.

**Um dump de schema que propõe reverter exatamente a coluna que sua migration acabou de mudar quase
sempre é cache de metadata velho**, não mapeamento quebrado. Limpar o cache e conferir de novo antes
de "consertar" a entidade ou escrever uma segunda migration. Relacionado: rodar os testes costuma
migrar **só** o banco de teste — migrar o de desenvolvimento explicitamente antes de qualquer
verificação manual por ele.

## Configuração e ambiente

**Alterar um limite num arquivo de configuração de servidor web não prova nada sobre o ambiente
implantado — verificar quem de fato monta aquele arquivo.** Num caso real, o arquivo era montado só
pelo compose de desenvolvimento, enquanto o pod implantado rodava seu próprio proxy configurado por
outro repositório, sem aquele limite: o default de 1MB do proxy sobrepunha silenciosamente os 5MB da
aplicação. Verificar ponta a ponta contra o ambiente real — o upload de mais de 1MB devolvia o HTML
de erro do proxy e nunca chegava à aplicação.

**Ler configuração de infraestrutura de `origin/master`, não do checkout local.** Um checkout 1281
commits atrás nomeou o destino errado na primeira versão de um achado.

**O log do proxy pode capturar o que o log da aplicação nunca viu.** Um sidecar configurado para
registrar corpo de requisição e resposta grava credencial de qualquer endpoint que a carregue, por
mais limpo que esteja o log da aplicação. Conferir o formato de log do proxy antes de afirmar "nenhum
segredo em linha de log nenhuma" — e conferir para **quais destinos** ele vai, porque costumam ser
mais de um.

## Git

**Numa cadeia de branches empilhadas (A → master, B → A, C → B), mergear master numa branch *mais
alta* sem cascatear de baixo faz o GitHub mostrar os commits do master como se fossem o diff daquela
PR.** Num caso real, `gh pr diff <B> --name-only` listou controller, teste, spec e plano de outro
ticket. Mergear master na branch mais baixa primeiro, depois cada uma na de cima, e conferir com
`gh pr diff --name-only` antes de pedir review. Merge-base correto **não** pega isso — o vazamento é
o master assimétrico, não o empilhamento.

## Testes e documentação

**Quando um teste precisa de um mock com status ou corpo que o helper existente não suporta, estender
o helper com parâmetro opcional** em vez de montar o mock à mão dentro do teste. O mock artesanal
duplica a URL e o método que o helper já é dono, e costuma ser o único da suíte inteira.

**Não rebaixar uma construção da linguagem por palpite de linter.** Regras de análise estática
costumam ser específicas por arquivo; aplicar uma às cegas enfraquece a garantia sem ganho nenhum.
Verificar rodando o linter **no arquivo em questão**.

**Anotação de resposta bem-sucedida costuma ter default 200.** Numa ação de criação que devolve 201,
passar o status explicitamente, ou a doc gerada contradiz o comportamento real. Da mesma família:
anotar o schema de um formulário documenta as **propriedades**, não quais são obrigatórias —
declarar as obrigatórias, senão o front monta payload a partir de uma doc que diz que tudo é opcional.
