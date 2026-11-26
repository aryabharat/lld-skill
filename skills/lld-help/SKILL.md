---
name: lld-help
description: >
  Quick reference card for the LLD plugin: what each skill does, how to call
  it, and which reference file answers which question. Use when the user says
  "lld help", "what can the lld skill do", or asks how to use this plugin.
  One shot; changes nothing.
license: MIT
---

# LLD help

Print this card and stop. Change nothing.

**Skills**
- `lld`: design or refactor classes, APIs, data structures, concurrency and tests. Triggers by itself on design work. Example: "design the classes for a parking lot with weekday pricing".
- `lld-review`: design review of a diff, PR, files or design doc, with findings grouped Must / Should / Nice. Example: "lld review my staged changes".
- `lld-patterns`: pick or reject a pattern for a concrete situation, with the rejected alternative and a sketch. Example: "strategy or state for order status?"
- `lld-interview`: mock LLD or machine-coding interview (you answer, it interviews and scores), or coach mode. Example: "mock interview: rate limiter, 60 minutes".
- `lld-help`: this card.

**Agent** (Claude Code, Copilot CLI): `lld-designer` produces a full design document or runs a review in its own context.

**Reference files** (in `skills/lld/references/`): workflow, decision-index, principles-and-smells, patterns, concurrency-and-async, data-modeling-and-apis, testing, review-checklist, interview, and case-studies (17 worked designs from the course plus nearest-neighbour guidance for common problems).

**Without skill support** (Cursor, Windsurf, Cline, Copilot, Kiro, Zed and others), `AGENTS.md` or the host's rule file carries the compact always-on rules.

Source: distilled from Gaurav Sen's free InterviewReady Low Level Design course. Lesson numbers like [L18] in the references point to the course lesson a rule came from.
