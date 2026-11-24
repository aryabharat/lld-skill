# lld-skill

A low-level design (LLD) and machine-coding skill and agent for [Claude Code](https://claude.com/claude-code), built from the concepts taught in Gaurav Sen's free [InterviewReady Low Level Design course](https://interviewready.io/course-page/low-level-design-course).

It teaches Claude to approach LLD the way the course does: clarify, shortlist requirements, design objects and APIs first, reach for principles and patterns only when a real problem calls for them, then handle concurrency, tests and trade-offs.

## What's inside

```
skills/low-level-design/
  SKILL.md                         how to approach a problem + output format
  references/
    process.md                     interview / workflow steps and timing
    principles-and-smells.md       SOLID, DRY, composition; code smell -> fix table
    patterns.md                    ~15 patterns: when to use, when not to
    concurrency-and-async.md       locks, per-key threads, futures, retries, DLQ, back pressure
    case-studies.md                condensed designs for 16 problems
    review-checklist.md            run before presenting a design
agents/
  lld-designer.md                  agent with Design / Mock interview / Review / Pattern advice modes
```

Case studies covered: turn-based game engine, tic-tac-toe, chess, Splitwise, cache (TTL + LRU/LFU, request collapsing), event bus, message queue, rate limiter, Google logger, orchestration service, Google Calendar, Zerodha, Twitter, live scores, Zomato coupon engine, Zomato delivery assignment, GitHub DB schema.

## Install

```bash
git clone https://github.com/aryabharat/lld-skill.git
mkdir -p ~/.claude/skills ~/.claude/agents
cp -R lld-skill/skills/low-level-design ~/.claude/skills/
cp lld-skill/agents/lld-designer.md ~/.claude/agents/
```

Restart Claude Code. For a single project, copy into that project's `.claude/skills/` and `.claude/agents/` instead.

## Use

- Ask naturally: "Design a parking lot", "LLD for BookMyShow", "which pattern fits X?", "review this class diagram". The skill triggers on its own.
- For a mock interview or a structured review, ask for the `lld-designer` agent by name: "use lld-designer to run a 45-minute mock LLD interview on Splitwise".

## Notes

- These are my own distilled notes and summaries of the course's ideas, not transcripts. All credit for the material goes to Gaurav Sen and InterviewReady; take the course for the full explanations.
- Three lessons (a Strategy pattern implementation video, and the mock LLD and IRCTC sessions with Keerti) had no captions and are not reflected here.
