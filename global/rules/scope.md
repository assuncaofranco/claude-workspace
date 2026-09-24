# Escopo

O que está dentro e fora de um ticket. Carregado no passo 7 (implementar) e no 13 (review).

## A regra

Achar um defeito fora do escopo **não** autoriza corrigi-lo. Nem depois de investigar, nem quando a
correção parece obviamente certa, nem quando é pequena. **Reportar e seguir.**

Vale para escopo no sentido amplo: a descrição do ticket, e também a spec e o plano que nós mesmos
escrevemos — cujo objetivo é entregar o ticket, não consertar o que vimos de errado no caminho.

**Por quê:** em sistema que toca dinheiro, um comportamento "errado" em produção com frequência está
errado por causa de dado antigo que ninguém vai auditar a tempo, e o código tolerante é o que mantém
tudo de pé. Endurecer esse código transforma dado sujo e inofensivo em indisponibilidade.

O caso que originou a regra (CLS-1872, 2026-09-21): propus fazer uma factory lançar exceção quando
falta chave na configuração, em vez de virar `null` em silêncio. Tecnicamente melhor. Mas a factory
está no caminho do jogador abrindo jogo, e qualquer configuração antiga sem uma chave adicionada
depois pararia de abrir jogo. Prejuízo milionário para resolver um problema que não era do ticket.

**Como aplicar:** reportar o achado com o que foi visto e por que parece defeito; não abrir branch,
não incluir no diff, não "aproveitar que já estou no arquivo". Se for grave, dizer que é grave — a
decisão de abrir ticket é do Lucas.

## A exceção: asserção que cobre o payload inteiro

Existe **um** caso em que "não mudar o que o ticket não precisa" não vale: quando um teste afirma um
payload completo e o seu acréscimo o quebra. Aí não há como passar adicionando só o que é seu — o
teste não permite alteração parcial, por construção.

Reconciliar tudo, e **avisar quando a parte herdada for grande**: um ticket de duas constantes com
sessenta linhas de diff no teste precisa dessa explicação, e o tamanho é fato sobre a dívida
acumulada, não sobre a sua mudança.

O que distingue esta exceção de "aproveitar que estou no arquivo": você não escolheu tocar no resto,
a asserção obrigou. Se dá para passar mexendo só no seu, a regra geral volta a valer.

O detalhe de qual teste, e por que a dívida cresce sozinha, fica no overlay do projeto.

## Corolário: mudança fora do padrão existente

Seguir o padrão que o código já usa para funcionalidade equivalente, a menos que algo tenha de fato
mudado — uma biblioteca compartilhada nova que supera a abordagem antiga, por exemplo.

Qualquer decisão de divergir **tem** que ficar documentada na spec do ticket, não só no chat. Uma
divergência não registrada vira, no próximo ticket, um segundo padrão que ninguém sabe explicar.
