# debate CLS-3916 — 2026-11-16 07:32

**Objetivo**

Hoje uma promoção só dá bônus. Com o CLS-3916, ela também passa a dar um presente físico sozinha, sem o operador registrar nada à mão.

**Premissas**

1. **Gift** é um presente (um item físico, por exemplo) dado a um jogador. Hoje o operador só consegue registrá-lo à mão, na página do jogador.
   `CLS-3916` → Problem statement: *"gifts ... are recorded only from the player page"*

2. **Promoção** é uma regra que premia o jogador automaticamente quando ele cumpre uma condição, como depositar dentro de uma faixa ou indicar um amigo. Hoje o prêmio só pode ser bônus.
   `CLS-3916` → Problem statement: *"issue promotion rewards only as bonus offers through the wallet"*

3. O CLS-3247 criou a **configuração de gift**, um modelo de presente reaproveitável, com nome, valor, moeda e estoque. Só que ele deixou as promoções de fora.
   `CLS-3916` → Problem statement: *"CLS-3247 gives gifts a gift reward configuration but leaves promotions out"*

4. Então, se o operador quer dar um presente a quem cai no tier VIP de depósito, ele precisa acompanhar as promoções e registrar cada gift à mão. Isso derruba a ideia de premiar automaticamente, e o gift perde o vínculo com a promoção que o gerou.
   `CLS-3916` → Problem statement, última frase

**Inferência**

Por isso, a story junta as duas pontas: o gift vira um tipo de prêmio da promoção, apontando para uma configuração de gift.

```
Operador, no BO
  └─ edita a promoção, escolhe "Gift" e uma configuração
     (só as ativas, do domínio, na moeda da promoção)
          │
Jogador cumpre a condição
          │
A promoção marca o jogador como premiado
  ├─ bônus da mesma faixa → saem como hoje
  └─ gift → criado já como "claimed", com nome, valor e moeda
            copiados da configuração; "criado por" = a promoção
          │
O gift aparece na aba Gifts do jogador e em Gifts to order (CLS-3865)
          │
O operador conclui ou cancela o gift como faz com qualquer outro
```

A spec dá ao gift o mesmo tratamento do bônus de promoção. O estoque esgotado, a falta de carteira do jogador na moeda e o status do jogador não bloqueiam o gift. A única exceção vem da configuração: se ela foi desativada ou apagada, aquele gift é pulado com log, e o resto do prêmio sai normalmente.

A Multiplus fica de fora, e o site da marca não mostra o gift. Uma faixa cujo único prêmio é um gift aparece para o jogador como uma faixa sem prêmio.

**O que falta**

O que eu disse sobre Gifts to order vem do nome e do critério de aceitação ("completed, canceled"). Não li o CLS-3865.

---

Aviso do conector: a conexão com o Atlassian ainda usa o endpoint V1, que está depreciado e sai em 2027-03-01. Para corrigir, remova o conector oficial e adicione de novo pelo diretório de conectores do Claude. Se for um conector customizado, aponte para `https://mcp.atlassian.com/v2/mcp`.
