---
description: Explicar do zero, em camadas, quando o Lucas não entendeu uma explicação por falta de conhecimento prévio do domínio. Começa pela necessidade de negócio e pelo sistema inteiro na versão mais simples que a atende, e acrescenta uma camada por problema real, cada peça nascendo da necessidade que a criou (estrutura de Reigeluth, motor do método genético). Usar depois de um explain que não funcionou porque faltava base, ou quando ele diz que não sabe o que são as peças.
argument-hint: <o que explicar — vazio usa o último assunto da conversa>
---

# elaborate

`explain` é o padrão e continua sendo. Esta skill entra **depois** dela, quando a explicação não
funcionou porque faltava base: ele não sabe o que são as peças, e premissa sobre peça desconhecida
não se sustenta.

A fronteira com a `explain`: lá, um conceito que falta no meio do caminho é explicado ali mesmo, e a
explicação segue. Aqui, o que falta é o domínio inteiro, e é ele que se monta do zero.

## Por que existe

Oncall de 2026-11-11, alerta de under-replicated partitions no Kafka. A `explain` produziu premissas
corretas ("cada partição tem um líder, os outros copiam"), em lista paralela, sem dizer que
necessidade cada peça atende, e usando "tópico" e "partição" sem nunca mostrar o que eram. Nas
palavras dele: explicar que um líder faz alguma coisa e outros copiam, sem dizer as necessidades, é
um erro grosseiro.

Comparamos três teorias: o método genético (Toeplitz), a aprendizagem significativa (Ausubel) e a
teoria da elaboração (Reigeluth). Ele escolheu a de Reigeluth depois de ver a mesma explicação do
Kafka montada nela. O exemplo do fim da página é essa versão.

Mas a forma é um híbrido, e é o híbrido que funciona: a **estrutura** é de Reigeluth (o sistema
inteiro primeiro, depois camadas), o **motor** é do método genético (cada peça nasce do problema que
a tornou necessária). Reigeluth puro adiciona complexidade retirando uma simplificação, sem exigir a
necessidade; aplicado sozinho, devolve o "líder faz, outros copiam". Quando as duas teorias puxarem
para lados diferentes, vale a necessidade.

## A forma

Quatro partes, nesta ordem.

**1. Epítome.** Abre pela necessidade de negócio que faz o sistema existir, numa frase sem nome de
sistema ("precisamos avisar muitos lugares de um mesmo evento, cada um tratando do seu jeito"). Só
depois vem o sistema inteiro, na versão mais simples que ainda atende essa necessidade. Não é um
resumo nem uma introdução: é o caso real com tudo que complica tirado. Só com palavras que ele já
usa. Um diagrama pequeno. Se o nome técnico entra, entra **depois** de a coisa ter sido mostrada
("esse caderno guardado numa máquina é o Kafka").

**2. Camadas.** Cada camada abre com **uma complicação real**, o que dá errado na versão anterior,
e mostra o que ela muda no desenho. O nome da peça nova vem por último, como rótulo de algo que ele
já viu. No máximo um termo novo por camada. Valor real do caso (contagem, nome de tópico, horário)
entra com a prova ao lado.

**3. Síntese.** Um diagrama com todas as camadas juntas, aplicado ao caso que motivou a pergunta.
É aqui que o alerta, o bug ou a decisão aparecem, já com todas as peças conhecidas.

**4. O que falta.** Só quando há algo não verificado ou inferido. Mesma regra da `explain`.

Parar na camada que o caso precisa. Uma camada que a síntese não usa custa a atenção dele e não
compra nada.

## Antes de enviar: três checagens

1. **Termo antes da camada.** Listar todo termo técnico. Cada um tem que aparecer pela primeira vez
   como rótulo, no fim da camada que mostrou a coisa, ou ter vindo dele nesta conversa. Termo usado
   antes da própria camada reprova. Foi o "tópico" de 2026-11-11.
2. **Camada sem complicação.** Tirar a primeira frase de cada camada. Se o resto ainda se lê bem
   sozinho, a camada é definição, não elaboração. Reescrever começando pelo que quebra. Foi o
   "líder faz, outros copiam".
3. **Epítome sozinho.** Só com o epítome, ele conseguiria dizer a outra pessoa **para que** o
   sistema existe e como ele funciona na versão simples? Se falta o para quê, o epítome começou no
   mecanismo, que foi o erro da primeira versão do exemplo abaixo. Se falta o como, é uma introdução.

Evidência, idioma e correção de premissa errada seguem a seção Rules da `explain`.

## Exemplo: Kafka, 2026-11-11

```
Epítome   precisamos enviar notificações → existe o notification; elas vão para muitos
          lugares, cada um tratando do seu jeito → o notification escreve num caderno
          guardado numa máquina; vários sistemas leem, cada um com seu marcador;
          ler não apaga → Kafka
Camada 1  vários assuntos, cada leitor quer só os seus → um caderno por assunto → tópico
Camada 2  um caderno muito escrito vira fila de espera → dividir em partes → partição
Camada 3  a máquina pode morrer → 3 máquinas, cada parte em mais de uma → broker
Camada 4  várias cópias, mas a ordem tem que ser uma → só uma recebe escrita → líder
Camada 5  uma máquina some → alguém passa as partes dela adiante → controller
Camada 6  uma cópia a menos, mais uma queda perde dado → avisar → under-replicated
Síntese   broker 1 sai às 12:10, controller redistribui, alerta, volta às 14, broker 3 às 24
```
