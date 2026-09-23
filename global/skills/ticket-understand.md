---
description: The mandatory first step for any ticket (feature or fix) — a short, colleague-style conversation to understand the business need and the current logic before any code gets written.
argument-hint: <TICKET or description>
---

# ticket-understand

Entry point for any ticket work — feature, fix, review, or test. Do not skip straight to "here's the description, write the code": that's exactly the pattern that has produced fixes that solve the surface problem but pile up technical debt, because no one checked what the change actually does to the business logic first.

## How this conversation runs

This is a **debate between colleagues**, not a report. Concretely:
- Short exchanges. One idea or one question at a time — never a long analysis dumped in one message.
- Give an actual opinion, not just agreement. If the user proposes something and you see a problem or a better option, say so — the point of the conversation is a second, independent perspective, not a rubber stamp.
- No AI-verbose filler: no restating what was just said, no padded preambles, no trailing recap nobody asked for.
- Details go in the ticket's own spec/plan output once you get there — not spelled out wall-of-text in the chat before that.

## Steps

1. **Get the ticket.** Take it from `$ARGUMENTS`. Check `memory/tasks/<ticket>/` first — prior context (scope, gotchas, decisions already made) may already exist from earlier work on it. If the ticket id names or implies a parent ticket (e.g. `CLS-1746-CLS-2008`, where `CLS-1746` is the parent) and no detailed description has been given yet, ask: "Lucas, você já viu se não há descrição no ticket pai?" — the parent ticket is often where the real requirements live, and the child's own description can be a one-line gist that hides the actual scope. If there's no description anywhere, ask for one — but if a detailed description isn't available either way, proceed to step 2 anyway with whatever is known (a ticket id and a one-line gist is enough to start).

2. **Understand the current business logic and the delta.** What does the system do today, and what is this ticket actually supposed to change? This is a back-and-forth with the user — they own product intent and business rules that aren't recoverable from the code alone; you own reading the code. Explore only the domain classes the ticket actually names or implies plus their direct collaborators — a full architectural survey of the service wastes tokens on controllers/forms/normalizers that have no bearing on this ticket. Use an Explore agent only when the relevant files are genuinely unknown, not as a default.

3. **Confirm you're aligned before moving on.** Once the business logic and the intended change are clear between you and the user, that's the signal to move to `ticket-matrix` — enumerate every variant the change touches before anything gets specced — then scenario-building (`ticket-test`) and only after that, code (`ticket-code`).

While reading the code in step 2, note the branch points you hit — type enums, offering methods, states, flags. Don't enumerate them here (that's `ticket-matrix`), just don't lose them.

## Handoff — do not recreate spec/plan here
Each Celesta service already has its own `/spec` and `/plan` (or `_specs/`/`_plans/` equivalents) in that service's `.claude/commands/`. Once this conversation reaches alignment, run that service's own `/spec` and `/plan` — don't write a competing spec here. If you're not sure which convention a given service uses, check its own `.claude/commands/` before assuming `_specs/`/`_plans/` or `sdd/`.

## Next
Hand off to `ticket-matrix`.
