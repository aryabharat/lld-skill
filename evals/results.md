# Eval results

## 2026-11-26: Opus 5.5, four prompts, one run each, with vs without the plugin

Prompts P1-P4 correspond to cases 1, 2, 5 and 6 in [cases.md](cases.md). Same model, same prompts. "Without" was told to use no skills; "with" read `skills/lld/SKILL.md` and the reference files it pointed to (patterns, concurrency, three case studies). Single run, hand-scored, so treat it as a smoke test, not a benchmark.

| Prompt | Without | With |
|---|---|---|
| P1 parking lot fees + concurrent arrivals | Strategy per vehicle type, clock injected, a lock around allocation. No rejected alternatives, two tests. | Price table plus an ordered adjustment list (and why order matters), money in minor units, clock injected, claim-by-compare-and-set plus a conditional DB update so exactly one car wins, 7 rejected alternatives with reasons, 6 tests with exact numbers. |
| P2 add "draw after 50 moves" to an if-chain | Rule list refactor, wins before draws. Already good. | Same refactor, plus: names the OCP smell, rejects a sixth `if` / a wrapper layer / a `Set<Rule>` with reasons, puts the move count on the owner, flags that 50 moves never happens on 3x3 and the ply-vs-round ambiguity, and writes before/after tests that pin rule order. |
| P3 Builder for Point(x, y) | No, use a record. | No, use a record; rejects Builder by name and says when it starts to pay. |
| P4 State pattern for order status | Enum transitions plus listeners. | Runs the course's State test, picks an enum transition table plus an append-only status log anyway (states have no distinct behaviour), Observer for multi-subscriber notifications run after commit, a conditional update on current status for races, and says when State would start to pay. |

What the plugin adds on a strong model: explicit rejected options, ownership of data, ordering and race handling, deterministic tests, and the clarifying questions. What it costs: answers about twice as long (1.8k vs 3.6k words across the four). The base model was already right on the headline choice in all four.

To reproduce: run each prompt in [cases.md](cases.md) in a fresh session with and without the plugin and score the "Must show" bullets.
