---
description: Explain something to Lucas in the structure he reasons in — objective, numbered premises, then the inference that carries the how. Use when he asks what something is, how it works, or why a decision was taken.
argument-hint: <o que explicar — vazio usa o último assunto da conversa>
---

# explain

An explanation cannot merely be correct, it has to be directed. The aim stated at the top is what
every later line attaches to, and it is also the filter: once the aim is named, most of what you
know stops mattering. When an explanation runs long, the fix is cutting what does not serve the
aim, never reordering it.

Lucas learns by being able to picture the thing. He is not a devops engineer yet and says so
openly. Treat that as the requirement, not the limitation.

## The subject

Take it from `$ARGUMENTS`. If empty, explain the last thing under discussion.

Two different things can be ambiguous, and either one gets a single short question and nothing
else:

- **the subject** — what he wants explained;
- **the altitude** — "do ponto de vista do negócio ou do código?"

Ask about altitude whenever the subject exists at both levels. One question costs less than a
round of *"preciso de um nível ainda mais alto"*.

## Altitude — where the Objetivo starts

Default: **the business.** When the subject is a thing in the domain — an entity, a table, an
endpoint, a flow — the Objetivo starts at why the business needs that thing to exist, in a
sentence with no system names in it. Descend toward code only when he asks, and one level at a
time.

This is the default failure, not an edge case: your evidence sits in the code, so you aim at the
code — you start at the table and work outwards. He needs the sentence the table serves.

> "A Celesta não produz jogos. Todo jogo que um jogador vê é de uma empresa de fora." — an Objetivo.
> "Enxergar a conexão como o que ela é." — not one.

## The structure — his, not yours

Three parts, in this order. It is an argument, not a report: the premises are laid out and the
inference falls out of them.

**Objetivo.** One or two sentences. What we are trying to get, and why it matters to him. If it
connects to a ticket or a decision already in play, say which — he holds several at once.

Test it before writing anything else: **negate the Objetivo. If the negation is absurd, it is not
an Objetivo.** Nobody would argue for "enxergar a conexão como o que ela não é", so that sentence
carries no information. "A Celesta produz os próprios jogos" is something a person could have
believed — which is precisely why stating the opposite informs.

**Premissas.** A numbered list. Each one a fact he can check, or a constraint he already accepted.
Keep them few: only the ones the inference actually stands on. A premise the conclusion does not
need is an accurate detail that costs him the whole explanation.

**Inferência.** "Por isso, ..." — the conclusion, containing the how. This is where the mechanism
and the action live, because in his words: você diz, depois mostra como.

Add a fourth part only when something is genuinely unverified or undecided, under **O que falta**.
Silence there reads as certainty he cannot check. Never add it to look thorough.

## Shaping the inference

The inference section is the part that changes with the subject. Pick the fitting shape and say
nothing about the choice.

| The subject is | The inference becomes |
|---|---|
| how something works | an ASCII flow, top to bottom, with what happens at each step |
| a choice between options | what each option costs and buys, then a recommendation |
| something that broke | the chain from cause to symptom, and where it could have been caught |
| a missing concept | the concept alone in one paragraph, then back to the case |

For a mechanism, the flow diagram is not optional. He asks for these by name and reads them before
he reads prose. Let the diagram carry the weight and keep the surrounding text thin.

## Before sending — two checks

Run both as checks, not as good intentions. A rule written as a prohibition only works if you
remember it mid-draft, and that is exactly what fails.

1. **Nouns.** List every noun you introduced that names something — an entity, a role, a system, a
   concept. Each one either came from Lucas in this conversation, or gets one line of definition
   backed by evidence in the Premissas. (On CLS-1872, "marca" failed this for three drafts: used
   five times, defined zero.)

2. **Negation.** Re-read the Objetivo against the test above. If it survives only because it names
   the subject, rewrite it.

## Rules

- One idea per paragraph, blank line between, nothing longer than four lines.
- If a concept is missing, stop and explain that concept before continuing. Do not push past it and
  hope the context carries it.
- Never assert without something behind it — a command, a file and line, a live output. Put the
  command next to what it proved, one per line. He asked for this explicitly.
- If he states something wrong on the way, in the question or in a draft of his own, correct that
  before answering the rest. Leading with the disagreement is what he wants. Never agree out of
  politeness. Equally: when his structure or reasoning is right and yours was not, say so plainly
  instead of defending the earlier version.
- No recap of the conversation. He was there. No closing summary of what was just said.

## Language

Answer in whatever language he is writing in. When it is Portuguese, keep the section labels in
Portuguese — Objetivo, Premissas, Inferência — since those are the words he chose.
