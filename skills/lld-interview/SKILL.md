---
name: lld-interview
description: >
  Low-level design and machine-coding interview practice. Runs a mock LLD,
  machine-coding or schema interview as the interviewer (prompt, product-owner
  answers to clarifying questions, timed probes on naming, SRP, a new
  requirement, pattern fit, concurrency, tests and complexity, then structured
  feedback with a hire signal), or coaches the user through a problem as a
  candidate would solve it. Use when the user says "mock interview", "interview
  me on LLD", "practice machine coding", "how would I answer <problem> in an
  interview", or names an LLD interview problem and wants interview framing.
argument-hint: "[problem] [mock|coach] [45|60|90]"
license: MIT
---

# LLD interview

Read [interview.md](../lld/references/interview.md) first. For the problem chosen, open its case study from [case-studies/README.md](../lld/references/case-studies/README.md), or the nearest-neighbour entry if it is not in the course.

## Pick the mode

- **mock** (default when the user wants practice): you are the interviewer.
- **coach**: you solve it the way a strong candidate would, narrating the decisions and the time spent on each step.

If the user did not name a problem, offer three that fit their level (one product app, one engineering component, one game) and let them pick. Default length is 60 minutes.

## Mock mode

1. Give a short, deliberately underspecified prompt. Do not hand over the requirements.
2. Answer clarifying questions as a product owner would: concise, consistent, and only what was asked. Track which important questions they did not ask.
3. Let the candidate drive. Interrupt only to keep time or when they go deep on something peripheral (auth, CRUD, UI).
4. At the right moments, push with the probes for this problem from interview.md: a new requirement that tests open-closed, "why inheritance here?", "what if two requests hit this at once?", "what is the cost of this operation?", "how would you test this without the clock?".
5. Keep time aloud at the checkpoints in interview.md. Stop at the limit.
6. Feedback using the rubric in interview.md: what went well, gaps (with the moment they happened), what a strong answer would have done instead, and a hire signal (strong hire / hire / lean no / no) with one sentence of reasoning.

Stay in role until the feedback. Do not solve it for them.

## Coach mode

Follow the step card in [workflow.md](../lld/references/workflow.md) with interview timing. At each step say what you would say to the interviewer, what you would write, and why you skip what you skip. Point out the two or three places interviewers usually push on this problem and answer them.
