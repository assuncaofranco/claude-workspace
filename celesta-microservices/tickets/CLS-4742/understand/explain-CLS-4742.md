# explain CLS-4742 — 2026-11-16 07:22

**Objetivo**

Quem altera uma configuração de recompensa no BO precisa saber, antes de alterar, quais cenários e promoções dependem dela. Hoje não tem como saber. O CLS-4742 é isso, dentro do épico de gift (CLS-3250).

**Premissas**

1. Uma **configuração de recompensa** é um modelo de recompensa (free bonus, free rounds, bonus on deposit, gift) que o usuário do BO cria uma vez e reaproveita em vários lugares.
2. Quem usa esse modelo: cenários, pela ação *Offer reward*, e promoções, pelas listas de recompensa (Deposit tier, First bet insurance, Multiplus, Refer a friend, Instant reward). Desde o CLS-4034, o gift de cenário também exige uma configuração.
3. Se a configuração for desabilitada ou apagada, ela é recusada na hora de oferecer. Nada avisa quem desabilitou: o jogador simplesmente fica sem a recompensa.
4. A página de detalhe da configuração não mostra quem a usa. Hoje o jeito é abrir cada cenário e cada promoção.
5. A página de segmento já resolve o mesmo problema com um card *Linked assets*, e a spec manda copiar esse card como está.

`getJiraIssue CLS-4742` → todas as premissas vêm da descrição (Problem statement, Scope e AC).

**Inferência**

Por isso, a página da configuração ganha um card *Linked assets* com os cenários e as promoções que a usam. O card **só informa**: desabilitar e apagar continuam funcionando como hoje, sem aviso e sem bloqueio (está no OUT). A aposta é que a pessoa vai olhar o card antes de mexer.

```
BO user abre a configuração X
        │
        ▼
[F] backoffice-front ── card Linked assets (4830)
        │
        ▼
[B] backoffice ── repassa o filtro "usa X?" (4829)
        │
   ┌────┴────────────┐
   ▼                 ▼
[C] scenario      [D] promotion
cenários com      promoções com X em
Offer reward = X  qualquer lista de recompensa
(4827)            (4828)
```

Cada serviço já tem a sua lista. A mudança é fazer essas listas aceitarem o filtro "usa a configuração X", e o front juntar o resultado.

Fica fora: gift de promoção (o CLS-3916 adiciona ao card quando for construído), uso por segmento ou por bulk offer, e contagem de uso na lista de configurações.

**O que falta**

A premissa 3 (recusar na hora de oferecer) é o que a spec diz. Ainda não conferi no código.

---

Aviso do conector: a conexão com o Atlassian ainda usa o endpoint V1, que está depreciado e sai em 2027-03-01. Para corrigir, remova o conector oficial e adicione de novo pelo diretório de conectores do Claude. Se for um conector customizado, aponte para `https://mcp.atlassian.com/v2/mcp`.
