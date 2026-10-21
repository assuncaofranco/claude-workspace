---
description: List what Lucas did on a given day, from the Claude Code transcripts, as a short list for the daily standup. Use when he asks what we did yesterday, on a date, or for his daily.
argument-hint: <data AAAA-MM-DD — vazio usa o último dia útil>
---

# daily

Lucas uses this for the daily. The point is the small things: a review answered in passing, a
message drafted for someone, an alert triaged. Those are what he forgets, and they are also what a
transcript keeps and the board does not.

## Source

```bash
~/Desktop/celesta-projects/claude-workspace/global/scripts/daily-log.sh $ARGUMENTS
```

It prints one block per session of that day: local time span, ticket ids ranked by mentions, and
his messages. Empty argument means the last working day (Monday reads Friday).

The ticket count is a hint, not the answer: a session that searches old conversations mentions
every ticket it finds. Name the session by what his messages ask for.

Where his messages don't show the outcome (pushed? answered? concluded?), read the end of that
session's assistant text in the transcript before guessing. If the ticket has
`memory/tasks/<ticket>/`, take the current state from there.

## Output

Two lists, the same items in the same order: first in Portuguese, then in English. Nothing else —
no prose report, no recap, no headers.

One bullet per theme, never per session: everything on the same ticket or epic is one line, all
oncall alerts of the day are one line, and process changes made while working a ticket go inside
that ticket's line. Several sessions on one theme still make a single bullet (2026-10-21: two oncall
bullets and an SDD bullet split from CLS-3150 read as duplicates). Each bullet is `<ticket ou assunto>: <o que foi feito>`, one
line, plain text, no bold. Reviews and tests of other people's tickets go in the same list, not a
separate section. Pure lookups ("busque nossa conversa sobre…") stay out.

```
- CLS-2485: DI escrito no ticket
- CLS-3835: Newman no local e no PP1, decisão pelo 400, testes corrigidos na branch do Socrates
- CLS-850: review dos PRs da wallet e do Proteus
```

```
- CLS-2485: wrote the deploy instructions on the ticket
- CLS-3835: ran Newman locally and in pp1, decided to return 400, fixed the tests on Socrates' branch
- CLS-850: reviewed the wallet and Proteus PRs
```

**Why this shape:** Lucas tried a bold PT list plus a spoken English paragraph first (2026-10-14 to
10-19). On 2026-10-20 he asked for a plain list of everything, then the same list in English, and
called it the best format so far.
