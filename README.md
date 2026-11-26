# lld

**Low-level design for coding agents.** Classes, APIs, data structures, design patterns, concurrency and tests, decided the way Gaurav Sen's free [InterviewReady Low Level Design course](https://interviewready.io/course-page/low-level-design-course) teaches them. Works in your real codebase and in interviews.

Most "design patterns" prompts make agents reach for patterns. This one makes them do what the course does: find the concrete problem first, pick the tool that removes it, say which option was rejected and why, and get correctness and thread safety right before extensibility.

```
You: add a "draw after 50 moves" rule to GameEngine.getState()

Without:  adds a seventh `if (...) return` to the method every feature already edits.
With lld: "getState is a chain of independent checks that every rule change edits (OCP smell).
           Move each check into a Rule object in an ordered list; the engine just loops.
           Rejected: wrapping getState in another layer, which adds a layer per feature.
           Watch out: if two rules depend on order, keep explicit if/else with named methods."
```

## How it was built

All 94 captioned videos of the course (about 30 hours, 97 lessons) were transcribed from the player's captions. One agent per video then analysed what the lesson teaches: the problem behind each technique, the decision rules (when, do, because, flips when), the rejected alternatives, the trade-offs, the smells, how it applies in production, and what interviewers probe. Those 94 analyses (~150k words) were merged by theme into the reference files below, deduplicated, with every rule tagged by the lesson it came from (`[L58]`). Where the instructor changed his mind or the course's own code had a bug (the logger's lock-while-waiting deadlock), the files say so and give the final position.

Three lessons had no captions and are not covered: the Strategy implementation video, and the two sessions with Keerti Purswani (mock LLD, IRCTC).

## What's inside

| Skill | Use it for |
|---|---|
| `lld` | The core. Triggers on design work: new module or service, feature on existing classes, pattern choice, thread safety, schema from features, interview problems. |
| `lld-review` | Design review of a diff, PR, files or design doc. Findings grouped Must / Should / Nice, each with a concrete failing case, the smallest fix, and the rule it breaks. |
| `lld-patterns` | "Which pattern fits?" in five lines, including "no pattern needed" and the rejected alternative. |
| `lld-interview` | Mock LLD / machine-coding interview (it interviews you, keeps time, probes, scores) or coach mode. |
| `lld-help` | Quick reference. |

Plus the `lld-designer` agent (Claude Code, Copilot CLI) for full design documents in their own context, and `AGENTS.md`: the compact always-on ruleset for agents without skills.

Reference library (`skills/lld/references/`, ~38k words, loaded on demand):

| File | What it answers |
|---|---|
| [workflow.md](skills/lld/references/workflow.md) | How to approach any design task; interview round types and timings; change requests on existing code |
| [decision-index.md](skills/lld/references/decision-index.md) | ~180 decision rules, one line each, grouped by the situation you are in |
| [principles-and-smells.md](skills/lld/references/principles-and-smells.md) | SOLID, DRY and its overfitting trap, composition, naming; 40-row smell -> fix table; refactoring method |
| [patterns.md](skills/lld/references/patterns.md) | Picker table plus ~20 patterns: when, when not, sketch, the pitfall the course hit |
| [concurrency-and-async.md](skills/lld/references/concurrency-and-async.md) | Locks vs keyed executors vs snapshots, ordering, read-your-writes, futures, request collapsing, retries, DLQ, back pressure, fail-open |
| [data-modeling-and-apis.md](skills/lld/references/data-modeling-and-apis.md) | Entities and value objects, schema from access patterns, API signatures, choosing data structures |
| [testing.md](skills/lld/references/testing.md) | Deterministic tests, stubbing changeable algorithms, concurrency tests |
| [review-checklist.md](skills/lld/references/review-checklist.md) | Yes/no review questions with a severity guide |
| [interview.md](skills/lld/references/interview.md) | Round types, budgets, probes per problem, mock rubric |
| [case-studies/](skills/lld/references/case-studies/README.md) | 17 worked designs: game engine, tic-tac-toe, chess, Splitwise, cache, event bus, rate limiter, logger, orchestrator, calendar, Zerodha, live scores, Twitter, message queue, coupon engine, Git schema, delivery assignment; plus nearest neighbours for parking lot, elevator, BookMyShow and others |

## Install

**Claude Code** (two prompts):

```
/plugin marketplace add aryabharat/lld-skill
```
```
/plugin install lld@lld-skill
```

**Codex:**

```bash
codex plugin marketplace add aryabharat/lld-skill
```
```bash
codex plugin add lld@lld-skill
```

**GitHub Copilot CLI:**

```bash
copilot plugin marketplace add aryabharat/lld-skill
```
```bash
copilot plugin install lld@lld-skill
```

**Gemini CLI / Qwen Code:**

```bash
gemini extensions install https://github.com/aryabharat/lld-skill
```

**Agents that read `SKILL.md` folders** (Cline, Factory Droid, Freebuff, Command Code, Goose, Muse and others): copy every folder under `skills/` into the agent's skills directory (for example `~/.agents/skills/` or `~/.claude/skills/`). Copy all five together: the smaller skills point at `../lld/references/`.

**Rule-file agents** (always-on rules, no on-demand references):

| Agent | File |
|---|---|
| Cursor | `.cursor/rules/lld.mdc` |
| Windsurf | `.windsurf/rules/lld.md` |
| Cline | `.clinerules/lld.md` |
| Kiro | `.kiro/steering/lld.md` |
| GitHub Copilot (IDE) | `.github/copilot-instructions.md` |
| Antigravity | `.agents/rules/lld.md` |
| Zed, Amp, Jules, Junie, Codex extension, anything else | `AGENTS.md` in the project root |

Copy the file into the same path in your project. They are generated from `AGENTS.md`.

## Use

Ask normally. The core skill triggers on design work:

- "Design the classes for a parking lot with weekday pricing and concurrent arrivals."
- "Add refunds to this payment module without touching the settlement code."
- "Is this cache thread-safe?"
- "Strategy or State for order status?"
- `/lld-review` (or "lld review my staged changes")
- `/lld-interview rate limiter 45` or "mock interview me on Splitwise"

## Develop

```bash
npm test
```

The tests check manifest versions, skill frontmatter, that every relative link resolves, and that the host rule files match `AGENTS.md`. After editing `AGENTS.md`, run `npm run sync`. [evals/cases.md](evals/cases.md) lists prompts and the behaviours a good answer must show, for comparing answers with and without the plugin.

## Credit and license

The ideas belong to Gaurav Sen and InterviewReady; take the course for the full explanations, the code, and the three lessons not covered here. This repo contains only original summaries and decision rules written from the lessons, not transcripts or the course's code. MIT for this repo's text and scripts.
