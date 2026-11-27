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
- **Blind judging**: answers were shuffled to letters A-F per task and stripped of skill names and lesson tags. Each task got two independent judges with different shuffles, none of whom saw which setup wrote which answer ([bench/make_packets.py](bench/make_packets.py), [bench/JUDGE_BRIEF.md](bench/JUDGE_BRIEF.md)).
- **Rubric** ([bench/rubric.md](bench/rubric.md)), written before any answer existed: a per-task checklist of behaviours a senior reviewer expects, four 1-10 scores (correctness, design, decision clarity, proportionality), a list of technical errors, and a full ranking.

## Results

| Setup | Mean rank (1 best) | Wins | Checklist | Correctness | Design | Clarity | Proportionality | Words |
|---|---|---|---|---|---|---|---|---|
| **lld (this repo)** | **2.00** | **6/16** | 100% | **8.6** | **8.8** | **9.0** | 7.9 | 7.6k |
| malay44/lld-skills | 3.19 | 2/16 | 100% | 8.4 | 8.2 | 8.0 | 7.9 | 7.7k |
| qfzhao670 | 3.19 | 4/16 | 97% | 7.9 | 8.1 | 8.3 | 8.3 | 6.7k |
| tylerpayne | 4.00 | 0/16 | 97% | 8.1 | 8.3 | 8.4 | 6.2 | 9.2k |
| software-design-philosophy | 4.25 | 1/16 | 91% | 7.6 | 7.7 | 8.1 | 7.9 | 7.3k |
| no skill | 4.38 | 3/16 | 98% | 7.4 | 7.8 | 7.9 | 7.9 | 6.4k |

Mean rank per task (two judges each):

| Task | lld | malay44 | qfzhao670 | tylerpayne | sw-design-philosophy | no skill |
|---|---|---|---|---|---|---|
| T1 Parking lot | **1.0** | 2.0 | 4.5 | 3.5 | 4.0 | 6.0 |
| T2 Add a rule | 2.0 | 3.5 | 5.0 | 3.5 | 6.0 | **1.0** |
| T3 Builder? | 2.5 | 4.5 | **1.0** | 6.0 | 4.0 | 3.0 |
| T4 State? | 2.5 | 4.0 | **2.0** | 4.0 | 6.0 | 2.5 |
| T5 Review | **1.0** | 3.0 | 3.0 | 5.0 | 3.0 | 6.0 |
| T6 Cache | 2.5 | 2.5 | 5.5 | 3.5 | **1.5** | 5.5 |
| T7 Schema | **2.0** | 2.5 | 2.5 | 3.0 | 6.0 | 5.0 |
| T8 Refactor | 2.5 | 3.5 | **2.0** | 3.5 | 3.5 | 6.0 |

What the judges said about lld: the clearest decisions (problem, chosen tool, rejected option, when the choice flips), the smallest change that solves the task with the deferred refactor and its trigger named, and correctness details others missed (fee computed before the ticket closes, money in integer minor units, the clock read once, deliberate `ON DELETE`). In review it stayed inside the diff and tied severity to an observed failure. Where it lost points: proportionality on the larger design tasks, and the two pattern questions (2.5 each).

## How to read this

- **Judge noise is about +/-0.5 rank.** The same answers given to new judges moved by that much. lld's lead over the next two setups (1.19 ranks) is larger than that noise; the gap to the no-skill baseline (2.38) is clear.
- **lld was refined against earlier runs of this benchmark** (general rules on right-sizing, side-effect order and review severity, not task answers); the other skills were run as published.
- **One answer per setup per task.** More runs would tighten the numbers.
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

The results above combine the latest judging of each task: [bench/round2](bench/round2/summary.md) for T1-T4 and T6-T8, and [bench/round3-T5](bench/round3-T5/lld-T5.md) for the review task, rebuilt by `python3 evals/bench/charts.py`. Earlier development runs are kept in [bench/round1](bench/round1/summary.md).
