# Benchmark: lld vs other LLD skills

Run on 2026-11-26. One model (Claude Opus 5.5) for every setup and every judge.

## Setups

| Setup | What it is | Size |
|---|---|---|
| lld (this repo) | 5 skills plus a 55k-word reference library built from per-lesson analyses of the InterviewReady LLD course | large |
| [malay44/lld-skills](https://github.com/malay44/lld-skills) | 4 skills (lld, lld-build, lld-concurrency, lld-review) with references | ~60k words |
| [qfzhao670/low-level-design-skill](https://github.com/qfzhao670/low-level-design-skill) | One SKILL.md (SOLID + patterns) with two reference files | ~4k words |
| [tylerpayne/system-design-skill](https://github.com/tylerpayne/system-design-skill) | System-design interview skill with LLD implementation guidance | ~24k words |
| [luoling8192/software-design-philosophy-skill](https://github.com/luoling8192/software-design-philosophy-skill) | Ousterhout's *A Philosophy of Software Design* as one skill | ~3k words |
| no skill | The same model with no skill | - |

## Method

- **8 tasks** ([bench/tasks.md](bench/tasks.md)): parking-lot pricing and concurrent allocation, a feature on existing if-chain code, Builder restraint, the State pattern question, a code review, a concurrent TTL+LRU cache, a GitHub-style schema, and a growing discount class.
- **Answering**: one agent per setup answered all 8 tasks. It read only its own skill files, picked the skill whose description fit each task the way a harness would, and could not ask questions ([bench/ARM_BRIEF.md](bench/ARM_BRIEF.md)).
- **Blind judging**: answers were shuffled to letters A-F per task and stripped of skill names and lesson tags. Each task got two independent judges with different shuffles: 16 judges in all, none of whom saw which setup wrote which answer ([bench/make_packets.py](bench/make_packets.py), [bench/JUDGE_BRIEF.md](bench/JUDGE_BRIEF.md)).
- **Rubric** ([bench/rubric.md](bench/rubric.md)), written before any answer existed: a per-task checklist of behaviours a senior reviewer expects, four 1-10 scores (correctness, design, decision clarity, proportionality), a list of technical errors, and a full ranking.

## Results

### Round 1: lld v2 as first published

| Setup | Mean rank (1 best) | Wins | Checklist | Correctness | Design | Clarity | Proportionality | Words |
|---|---|---|---|---|---|---|---|---|
| malay44/lld-skills | **2.81** | 3/16 | 100% | 8.4 | 8.2 | 7.9 | 8.1 | 7.7k |
| lld (this repo) | 3.19 | 4/16 | 100% | 8.1 | 8.1 | **9.1** | 6.1 | 11.0k |
| qfzhao670 | 3.44 | 2/16 | 97% | 8.0 | 8.1 | 8.2 | 8.2 | 6.7k |
| tylerpayne | 3.50 | 3/16 | 97% | 8.2 | 8.2 | 8.2 | 6.7 | 9.2k |
| software-design-philosophy | 4.00 | 3/16 | 94% | 7.7 | 7.8 | 8.2 | 7.9 | 7.3k |
| no skill | 4.06 | 1/16 | 100% | 7.4 | 7.9 | 7.7 | 7.9 | 6.4k |

What the judges said about lld: the best decision clarity, but over-built. It refactored a one-rule change into a rule engine (T2), escalated an async redesign to must-fix in a review (T5), and ran 1.5-2x longer than the leader. They also caught real bugs: a ticket closed before its fee was computed, money passing through `double` in a helper, and a foreign key that blocked deleting a user.

### What changed between rounds

General rules, not task-specific answers ([SKILL.md](../skills/lld/SKILL.md), [lld-review](../skills/lld-review/SKILL.md), [AGENTS.md](../AGENTS.md)):
- Refactor toward extensibility only with evidence that the change will repeat; otherwise make the smallest clean change and name the deferred refactor and its trigger.
- Length budgets per question type; no diagram unless asked or more than five classes.
- A pre-code check for side-effect order, money types, reading the clock once, foreign-key delete behaviour, and prose matching code.
- Review severity: a broken design rule with no observed failure is should-fix at most; stay inside the diff.

### Round 2: lld after the fixes (other setups' answers unchanged, all re-judged by 16 new judges)

| Setup | Mean rank (1 best) | Wins | Checklist | Correctness | Design | Clarity | Proportionality | Words |
|---|---|---|---|---|---|---|---|---|
| **lld (this repo)** | **2.56** | 4/16 | 100% | **8.5** | **8.6** | **8.9** | 7.6 | 7.6k |
| qfzhao670 | 2.94 | 6/16 | 97% | 7.9 | 8.1 | 8.3 | 8.3 | 6.7k |
| malay44/lld-skills | 3.31 | 2/16 | 100% | 8.3 | 8.2 | 8.0 | 7.9 | 7.7k |
| tylerpayne | 3.62 | 0/16 | 97% | 8.2 | 8.3 | 8.4 | 6.3 | 9.2k |
| software-design-philosophy | 4.25 | 1/16 | 91% | 7.7 | 7.7 | 8.2 | 7.9 | 7.3k |
| no skill | 4.31 | 3/16 | 98% | 7.5 | 7.8 | 8.0 | 7.9 | 6.4k |

Per task, lld ranked 1.0 on parking lot, 2.0 on the feature change and the schema, 2.5 on Builder, State, cache and discounts, and 5.5 on the code review.

## How to read this

- **Judge noise is about +/-0.5 rank.** The competitors' answers were identical in both rounds, yet malay44 moved from 2.81 to 3.31 and qfzhao from 3.44 to 2.94 with new judges. lld's lead in round 2 (0.38 over qfzhao) is inside that noise. The gap to the no-skill baseline (1.75 ranks) is not.
- **Round 2 is not a neutral comparison.** lld was tuned once after seeing round-1 feedback; the competitors were not. The fixes are general, but treat round 2 as "after one iteration", not "out of the box".
- **One answer per setup per task.** More runs would tighten the numbers.
- **Code review (T5) was lld's weak task in round 2 (rank 5.5)**: it kept proposing an async redesign. The review guidance was then scoped further (blocking IO is must-fix only on reader or event-loop threads; no per-finding rule lines). A T5-only re-check with two fresh judges and a new shuffle ranked the new lld review **1st from both judges** (others unchanged: qfzhao, malay44 and software-design-philosophy 3.0, tylerpayne 5.0, no skill 6.0). Files: [bench/round3-T5](bench/round3-T5/lld-T5.md). The other seven tasks were not re-run after this change.
- **What every skill adds on a strong model is modest.** All setups, including no skill, hit 90%+ of the checklists. The differences are in correctness details, design judgement and right-sizing.

## Reproduce

Clone each competitor next to this repo, follow [bench/ARM_BRIEF.md](bench/ARM_BRIEF.md) once per setup (replace `<BENCH_DIR>`), then:

```bash
python3 evals/bench/make_packets.py
```

Run one judge per packet with [bench/JUDGE_BRIEF.md](bench/JUDGE_BRIEF.md), then:

```bash
python3 evals/bench/aggregate.py
```

Raw answers and every judge's JSON are in [bench/round1](bench/round1/summary.md) and [bench/round2](bench/round2/summary.md).
