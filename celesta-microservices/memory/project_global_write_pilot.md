---
name: project-global-write-pilot
description: "Desde 2026-11-11 o Lucas tem write em 64 repos (time \"Global write team\") e pega tickets do Team A no sprint 15-Beedrill; o propósito oficial ainda não foi dito"
metadata:
  node_type: memory
  type: project
  originSessionId: 62088cdd-c327-4fdb-8c35-d9d5e7834bae
  modified: 2026-11-12T15:41:49.171Z
---

Fatos (2026-11-11):
- GitHub: time `global-write-team` criado em 2026-10-30, 64 repos, 3 membros: JanisGruzis, lucasfranco83, modarche (provável Mykyta Odarchenko). Adicionado pelo Janis.
- Virgile (DM) passou ao Lucas os 6 primeiros tickets do Team A no sprint 15-Beedrill (16–27/11): CLS-4779 (story Paytech refund, Ready, sem split), CLS-1214 (story combinar saques num payout, Split) + sub-tasks CLS-4753 payment, CLS-4754 statistics, CLS-4755 wallet, e CLS-418 (task KPIs para statistics, Split). Épicos: CLS-3077 WDR, CLS-3250 Gift reward, CLS-3699 BQ MV sync costs.
- Contexto: em 2026-11-02 a liderança anunciou "concurrent SDD implementation" (um dev pega a story inteira e roda o SDD nas sub-tasks em paralelo). Em 2026-11-06 o Lucas teve de abrir PR por fork no celesta-segment por falta de write.
- Nenhuma página no Notion descreve o programa; o roadmap de IA (Notion, "AI Deployment Roadmap") fala em fase 4 = "AI executa, humano supervisiona".

Leitura (inferência, não confirmada): piloto de dev "cross-team" com SDD, onde o repositório deixa de ser barreira de time.

Fluxo para esses tickets: `global/skills/ticket-story.md` (criado 2026-11-11), com as três decisões do Lucas registradas lá.

Em 2026-11-12 virou formato só SDD (a empresa testando): execução numa conversa só com `/sdd-*`, avaliação na outra. Índice, ordem e avaliação: `celesta-microservices/sprints/15-beedrill/`; entendimento por ticket em `celesta-microservices/tickets/<KEY>/notes.md`. Na prática são 3 tickets: CLS-1214, CLS-4779, CLS-418, nessa prioridade: 4779, 1214, 418 (ordem do sprint, confirmada pelo Pedro Vasconcelos, PO e assignee das stories, em 2026-11-12).

**Modelo do time (2026-11-12):** nós fazemos todas as sub-tasks dos tickets, de qualquer time (B, C, F incluídos: BO, Gateway, Segment, backoffice-front); o que muda é que quem aprova e faz o merge é o time dono do repositório. Front incluído: confirmado pelo Mykyta, que rodou um épico inteiro no processo só SDD (2026-11-12). Perguntas: produto ao Pedro (brasileiro, em português); técnico ao Viorel (TL do A, romeno, em inglês).

**How to apply:** tickets do Team A são fora dos [[project-our-services]]; tratar com o fluxo normal de ticket, mas o deploy autoritativo é do TL do A (Viorel). Atualizar este arquivo quando o propósito for dito oficialmente.
