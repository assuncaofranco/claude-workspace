---
name: wallet-ownership-shift
description: celesta-wallet is shifting to time A as bonuses move to promotion; wallet changes get descoped from our tickets
metadata:
  node_type: memory
  type: project
  originSessionId: f6d4c80f-43d6-4e84-9cbd-0806044cdbd5
  modified: 2026-10-12T09:31:58.845Z
---

Até 2026-10 a celesta-wallet era dividida com o time A porque os bônus moravam lá e eram nossos. Com o bônus migrando para a celesta-promotion (flag `move_bonus_to_promotion`, ver [[cls2847-cls2848-matrix]]), vamos perdendo a wallet aos poucos.

Caso concreto: CLS-1788 (bônus em qualquer moeda). Os PRs da wallet CLS-3376 (#1897, #1898) foram fechados sem merge em 2026-10-08 por decisão, e a promotion #545 (CLS-3357) voltou os payloads de claim/refund para os do master. Consequência aceita: um bônus numa moeda em que o player não tem wallet cai na wallet mais antiga dele, com moeda diferente.

**Revertido:** em 2026-10-09 o Bohdan reverteu o corte na #545 (wallet de volta), e os PRs #1897/#1898 da wallet foram reabertos em 2026-10-12. Quem cortou foi o CLS-3371 (game), não o CLS-3376. O motivo da volta não foi registrado aqui. A tendência de perder a wallet segue valendo, mas não vale como regra automática de "wallet fora do escopo".

**Why:** a wallet está deixando de ser território nosso.

**How to apply:** num review ou num spec nosso, mudança de wallet sumir do escopo não é corte suspeito, é o esperado. Não cobrar a mudança, mas apontar a consequência para o lado da promotion.
