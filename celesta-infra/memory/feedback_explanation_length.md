---
name: feedback-explanation-length
description: "Lead with the answer in 3-5 lines; Lucas rejects long descriptive explanations, wants the reasoning to land on a conclusion"
metadata:
  type: feedback
  originSessionId: 79aa3c98-fb0c-4187-a15c-e4ac157378b8
  modified: 2026-09-10T16:27:28.501Z
---

Answer the question asked, in 3-5 lines, leading with the conclusion. Then stop — expand only if asked.

**Why:** Corrected three times in one session (2026-09-10), escalating: "escreveu muito, simplifica" → then, on a 7-paragraph explanation of why a Blue/Green deploy failed: *"sua explicação é cansativa e desprovida de lógica — um texto desse tamanho pra explicar algo que deve ser simples."* The complaint was not only length: walking through every mechanism in sequence reads as description, not reasoning. He wants the causal answer first, evidence under it.

**How to apply:**
- When he lays out his own mental model and asks "onde está o erro?", find the single step where his model diverges from reality and name it. Don't re-explain the steps he already got right.
- One short evidence block (log lines, event timeline) beats prose describing that evidence.
- This does NOT contradict [[feedback_teaching_style]] — grounding in real machines/files/processes is still right. Ground it in *fewer words*: the concrete detail belongs in the evidence block, not in narration around it.
- Applies to explanations. Operational safety checks (what will change in prod, what needs his go-ahead) are still spelled out fully — he has never pushed back on those.
