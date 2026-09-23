---
name: explanation-method
description: "How Lucas wants infra concepts explained — three-layer split (reality/record/intent), mechanism before conclusion, every claim backed by a command"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 282a851f-4219-4348-9a75-922710f55898
  modified: 2026-09-15T07:25:38.911Z
---

When explaining anything in infrastructure to Lucas, use these two habits. He named them as
what finally made a hard day's material click, and asked for them to be recorded.

**1. Separate the three layers explicitly.** Reality (what exists in AWS), record (what
Terraform wrote in its state), intent (what the code asks for). Almost every confusion in
practice is two of these being treated as one thing. Examples that landed: import writes to
the record without touching reality; a phantom plan diff is record-vs-intent disagreeing while
reality is already correct; drift is reality-vs-record.

**2. Mechanism before conclusion, and never assert without a command behind it.** Explain how
the thing works, then what follows from it. Run the command and show the output rather than
stating the result from memory — he checks, and he has been burned by confident-sounding
claims that turned out imprecise.

**How to apply:** keep answers short, he has said repeatedly he cannot read long text. Correct
a wrong premise before answering the question built on it, instead of answering the wrong
question politely. When he drafts his own explanation and asks for correction, fix the
technical structure but keep his wording and line of reasoning — he is going to say it out
loud, in his own voice. See [[feedback_explanation_length]] and [[feedback_teaching_style]].
