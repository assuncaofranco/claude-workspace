# 15-Beedrill — Team A

16–27/11/2026. Três tickets passados pelo Virgile em 2026-11-11. Formato: só SDD (ver abaixo).

## Tickets por épico

Agrupamento lido do campo parent do Jira em 2026-11-12. Se o Jira mudar, muda esta lista, não a pasta.

**CLS-3077** 🏧 WDR improvements
- [CLS-1214](../../tickets/CLS-1214/) combinar saques num payout (story) · sub-tasks 4753 payment, 4754 statistics, 4755 wallet

**Sem épico**
- [CLS-4779](../../tickets/CLS-4779/) refund automático Paytech (story)
- [CLS-418](../../tickets/CLS-418/) KPIs só da Statistics (task; a spec cita CLS-297, sem ligação no Jira)

**CLS-3250** (D-Team, PO Francisco), assumidos 2026-11-16, uma conversa por ticket
- [CLS-3316](../../tickets/CLS-3316/) motivo de oferta nas configs e bônus · 4743–4748
- [CLS-3916](../../tickets/CLS-3916/) gift como prêmio de promoção · 4767–4776
- [CLS-3865](../../tickets/CLS-3865/) editar valor e completar gifts · 4935–4944
- [CLS-4742](../../tickets/CLS-4742/) assets ligados na página da reward configuration · 4827–4830

CLS-3699 foi citado pelo Virgile e não tem ticket nosso.

## CLS-3250 — fila por repositório

Coordenada aqui; o detalhe de cada ticket fica na conversa dele. Plano roda tudo em paralelo (só lê
código). Implement roda em paralelo **entre** repositórios; **dentro** de um repositório, uma fila só,
porque o `sdd-implement` faz checkout no clone e o `make test` divide container e banco.

Prioridade: os quatro são High, prazo 02/12; desempata o rank do sprint: **3316 → 3916 → 3865 → 4742**.
Bate com o Blocks (3316 bloqueia 3916). Os bloqueios de fora (CLS-4032, 4034, 4035) estão Done.

| Repositório | Fila | Observação |
|---|---|---|
| promotion | 4743 → 4744 → **4828** → 4770 → 4771 → 4772 → 4773 → 4940 → 4941 | 4828 fora do rank: pequena, isolada, e destrava a 4829 do Charles. 3916 antes de 3865: as duas migram a entidade gift. 4772 espera 4768 e 4769 |
| backoffice | 4745 → 4774 → 4775 → 4942 → 4829 | 4748 entra quando a 4746 (front, Dimitris) fechar, sem segurar a fila |
| constants | 4767 → 4935 | cada merge gera tag: conferir o alias do pin antes do review e do release |
| job-library | 4768 → 4936 | idem |
| activity | 4769 → 4937 | |
| backoffice-front | 4830, 4943 → 4944 | 4746 e 4776 com o Dimitris |
| etl · statistics · terraform-bi · scenario | 4747 · 4938 · 4939 · 4827 (Charles) | um por repositório, sem fila |

**Regra em uso (Lucas, 2026-11-16), substitui a fila fixa acima, que fica só como referência:**

- entrega um pai por vez; o 3316 tem prioridade na execução, porque já começou;
- `sdd-plan` roda nos quatro pais em paralelo;
- o repositório fica livre quando o `sdd-implement` termina (veredito no PR, `sdd-reviewed`), não no
  push: os revisores leem a árvore de trabalho, e o implement corrige os achados no mesmo clone;
- liberou → aqui eu digo qual ticket roda o próximo implement naquele repositório: o primeiro pelo
  rank cuja sub-task ali não está bloqueada. Correção de review humano depois disso pede o clone de
  volta e passa na frente.

**Foco (Lucas, 2026-11-16 ~10:45): só CLS-3316 e CLS-1214, por falta de tokens.** 3916, 3865 e 4742
pausam onde estão; os agentes já rodando no 3916 terminam no rascunho e param.

Implement pode rodar em worktree, desde que haja **um stack por serviço** na máquina: o stack fica com
quem está com a fila daquele repositório.

**Plano também usa o clone (corrigido 2026-11-16).** O `sdd-plan` exige HEAD no master ou em `<KEY>`
para ler, e faz `checkout -b <KEY>` para escrever. Dois planos no mesmo repositório, ao mesmo tempo, no
mesmo clone se atropelam. O skill aceita o clone que você indicar, então todo `sdd-plan` roda num
worktree próprio: `git -C <repo> worktree add ../.worktrees/<KEY> origin/master`. Fora de `/tmp`, que um
reboot limpa (os do 1214, em `/tmp/cls1214/`, ainda existem e ficam). O clone principal fica no master,
para leitura. O implement continua no clone principal e em fila, porque o `make test` depende do
diretório.

Plano que lê o resultado de outro espera o rascunho dele (overlay). No 3865: 4940 e 4941 esperam os
rascunhos da 4770 e da 4773 (3916); a 4942 espera os da 4940 e da 4941; a 4943 e a 4944 esperam o da
4942. Em paralelo já: só da 4935 à 4939.

**CLS-1214 entra na fila (Lucas, 2026-11-16).** Retomado; sub-tasks 4753–4758 com o Lucas. Rascunhos e
estado em [tickets/CLS-1214/sdd.md](../../tickets/CLS-1214/sdd.md) (4753 commitado local, sem push).

| Repositório | Sub-task | Com o CLS-3250 |
|---|---|---|
| payment | 4753 | livre, roda já |
| wallet | 4755 | livre, roda já (depois do plano do 4753) |
| statistics | 4754 | divide com a 4938 (3865), que está longe: 4754 vai primeiro |
| backoffice | 4756, 4758 | entra na fila do backoffice pela regra acima; 4758 só depois do 4757 em produção |
| backoffice-front | 4757 | entra na fila do front |

O épico CLS-3077 não tem descrição. Pelas 19 stories, o tema é o ciclo do saque no BO: validar,
segurar, ordenar, pagar. O CLS-1214 é a parte de pagar.

## Ordem

A ordem do sprint (rank no Jira) é a prioridade, confirmado pelo Pedro em 2026-11-12:

1. **CLS-4779** — refund Paytech. Depende de credencial de sandbox da Paytech.
2. **CLS-1214** — combinar saques.
3. **CLS-418** — KPIs da Statistics.

A proposta anterior (1214 primeiro, para destravar o Time B) caiu: nós fazemos as sub-tasks do B
também, então não há ninguém esperando por nós.

## Formato só SDD

A empresa quer testar o formato só com o SDD; nós avaliamos. Decisão do Lucas, 2026-11-12.

| | Execução (conversa nova) | Avaliação (esta) |
|---|---|---|
| Recebe | só `/sdd-*` e correções em inglês | a saída de cada passo: transcript, Jira, git, PR |
| Faz | o que o SDD manda | confere contra spec e código, registra, escreve a correção |

Ciclo de cada passo:
1. Eu passo o comando; o Lucas roda na execução.
2. O SDD para (rascunho, pergunta, pedido de push). O Lucas avisa aqui.
3. Avalio e registro em [evaluation.md](evaluation.md), **antes** do próximo passo.
4. Erro: correção em inglês, curta, sem citar nosso fluxo; o Lucas cola lá. Volta para 2.
5. Sem erro: o Lucas dá o "sim" lá.

## Decisões que atravessam os tickets

| Data | Pergunta | Decisão e motivo | Quem |
|---|---|---|---|
| 2026-11-16 | CLS-1214 volta | retomado em paralelo ao CLS-3250, aproveitando payment e wallet, que nenhum dos quatro toca. Revoga a devolução de 2026-11-13 para o 1214; o 418 continua parado | Lucas |
| 2026-11-16 | paralelismo no CLS-3250 | uma conversa por ticket; plano em paralelo, implement em fila por repositório, coordenada aqui (seção acima). Ordem pelo rank do sprint, 4828 adiantada | Lucas (fila), Claude (ordem) |
| 2026-11-13 | parar os tickets do Time A | CLS-1214 e CLS-418 devolvidos para outro dev pegar: as 13 sub-tasks ficaram sem assignee e continuam em To Do; os pais seguem em Split, porque o split vale e quem pegar começa no `sdd-plan`. Nada tinha subido (sem branch, sem PR). Os rascunhos ficam só em `tickets/<KEY>/drafts/`. O componente A-Team das sub-tasks de outro time continua lá até o Lucas decidir | Lucas |
| 2026-11-12 | formato | só SDD na execução; avaliação de cada passo aqui, registrada antes do próximo. A empresa quer testar o formato | Lucas |
| 2026-11-12 | quem faz o quê | nós fazemos todas as sub-tasks dos tickets, de qualquer time (B, C, F incluídos); muda só quem aprova e faz o merge, que é o time dono do repositório. Component errado no Jira (3526) não bloqueia: ajustar quando formos trabalhar nela. Front incluído, confirmado pelo Mykyta, que rodou um épico inteiro assim | Lucas |
| 2026-11-12 | componente das sub-tasks | A-Team em todas, inclusive as de repositório de outro time (4756, 4757, 4758, 3527 trocadas; 3524 e 3526 já eram A). Pais CLS-1214 e CLS-418 só com A-Team. O título mantém o prefixo do time dono do repositório (`{B}`, `{C}`, `{F}`): muda só componente e assignee. O formato é o Lucas fazendo tudo; o componente segue quem faz | Lucas |
| 2026-11-12 | prioridade | a ordem do sprint: 4779, 1214, 418 | Pedro |
| 2026-11-12 | perguntas ao dono | nenhuma: falha do payout e aviso ao player respondidos pelo código da wallet; sub-tasks do 418 resolvidas pela regra acima | Lucas |
| 2026-11-12 | organização | ticket é a unidade (`tickets/<KEY>/`); sprint é índice e avaliação. Ticket atravessa sprint e épico muda no Jira | Lucas |
| 2026-11-11 | spec de outro com buraco | propor ao dono, ou editar pela fase do SDD com autorização expressa | Lucas |
