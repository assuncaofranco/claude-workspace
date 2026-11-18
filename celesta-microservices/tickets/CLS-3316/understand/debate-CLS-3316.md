# debate CLS-3316 — 2026-11-16 08:01

Depende de onde, e muda com o ticket:

- **Hoje, na configuração do bônus:** uma lista fixa de 31 chaves no código, igual para todas as marcas. O que estiver fora dela é recusado (`Assert\Choice` em `RewardConfiguration.php:282`).
- **Hoje, no gift:** uma lista por marca. A marca cria cada motivo na Administração, escrevendo o nome (texto livre, até 64 caracteres, sem repetir dentro da marca).
- **Depois do 3316:** tudo passa a usar a lista do gift. Texto livre só existe na hora de **criar** o motivo na Administração. Na configuração, na oferta e no cenário o motivo sempre é **escolhido num select**.

Boa ideia registrar as possibilidades no understand. Coloquei em `tickets/CLS-3316/understand/reasons.md`: as 31 chaves, as 10 antigas que só o front ainda traduz, os 4 motivos de gift do seed do 4163 e a diferença entre o que a spec e a 4744 mandam criar.

Uma coisa ainda não está verificada: quais dessas chaves aparecem de fato nas configurações gravadas. É o que decide a pergunta 1 ao PO. Dá para conferir no pp1 com o `db-query`, somente leitura.
