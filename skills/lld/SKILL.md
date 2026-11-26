---
name: lld
description: >
  Low-level design for real code and interviews: classes, objects, APIs, data
  structures, design patterns, SOLID, concurrency, async IO and tests, decided
  the way Gaurav Sen's InterviewReady LLD course teaches. Use when designing or
  refactoring a module, service, library or component (cache, queue, event bus,
  rate limiter, scheduler, logger, game, booking/payment/feed app); adding a
  feature to existing classes; choosing between inheritance, composition and a
  pattern; making shared state thread-safe; designing a DB schema from product
  features; or solving an LLD / machine-coding interview problem (parking lot,
  Splitwise, BookMyShow, chess, elevator). Not for distributed-systems HLD
  (sharding, capacity) except where it touches one component's internals.
license: MIT
---

# LLD

You design code that survives a pull-request review and the next three feature requests. Judge every choice by **readability, extensibility, correctness**. Principles and patterns are tools that come out of fixing a concrete problem: name the problem first, then the tool, then the option you rejected.

## 1. Classify, then follow that flow

| Task looks like | Start from | Then |
|---|---|---|
| Engineering component (cache, queue, bus, limiter, logger, scheduler, SDK) | the public API and its return types | data structures per operation -> threads/ordering -> failure handling -> tests |
| Product feature (Splitwise, Twitter, Zerodha, calendar, coupons) | the one method that delivers the core outcome | entities and services it needs -> main flow -> schema -> notifications as events |
| Game or simulation (chess, tic-tac-toe, snake and ladder) | the board/state object | common vs special behaviour -> inheritance vs composition -> rules as objects |
| Schema | product features -> objects | tables and indexes from the queries you will run |
| Change request or refactor on existing code | the smell the request exposes | principle that removes it -> smallest refactor -> tests before and after |

Workflow, timings and what to skip: [references/workflow.md](references/workflow.md).

## 2. The loop

1. **Clarify** with one concrete example. Write assumptions down. List every requirement, then shortlist the 3-6 that matter and name what you skip.
2. **API first.** Write the critical signature and its return type; work backwards to objects and fields. Result objects over booleans when there are more than two outcomes. Futures for anything that does IO.
3. **Objects.** One owner per piece of data, validated at its entry point; names that do not lie; nested or parallel maps become classes; inheritance only for true is-a; modes are fields or composed objects.
4. **Data structures and algorithm.** Pick from every operation's cost. Ranges and "first after T" need sorted maps; two access paths mean two indexes kept in sync. Simple algorithm first, name the optimal one.
5. **Extensibility check.** Pretend the next likely requirement arrives. If it forces edits to tested code, move the varying part out: rule list, strategy, event, builder, factory. If no change is likely, leave it simple.
6. **Concurrency pass.** List shared mutable state and give each a mechanism (whole-object lock, keyed single-thread executor, snapshot swap, concurrent collection). Request threads never block on IO. Retries only for retryable errors.
7. **Tests.** Inject time; script inputs; one unit at a time; the worked example as an exact-number test.

Every rule in the course, one line each, by situation: [references/decision-index.md](references/decision-index.md).

## 3. Where to look

| Need | File |
|---|---|
| SOLID, DRY, naming, composition, smell -> fix table, refactoring method | [principles-and-smells.md](references/principles-and-smells.md) |
| Which pattern fits, which to reject, sketches | [patterns.md](references/patterns.md) |
| Locks, keyed executors, futures, ordering, retries, DLQ, back pressure, caching policies | [concurrency-and-async.md](references/concurrency-and-async.md) |
| Entities, value objects, schema, indexes, API signatures, data-structure choice | [data-modeling-and-apis.md](references/data-modeling-and-apis.md) |
| Deterministic tests, stubs, concurrency tests | [testing.md](references/testing.md) |
| A known problem (17 worked designs + nearest neighbours for parking lot, elevator, BookMyShow...) | [case-studies/README.md](references/case-studies/README.md) |
| Reviewing a design or PR | [review-checklist.md](references/review-checklist.md) |
| Interview rounds, time budgets, probes, mock rubric | [interview.md](references/interview.md) |

Read only the files the task needs. For a known problem, open its case study before designing.

## 4. Non-negotiables

- Never edit tested core code to add a variant when a list of objects, a strategy or an event would take it as an addition.
- Never put a member on a base type unless every subtype supports it in that exact form.
- Never read the system clock in domain code or tests.
- Never block a request or reader thread on IO, and never wait on a future while holding the lock its completer needs.
- Never keep the same key in parallel maps; never put lists in a single DB column.
- Do not over-engineer: no config DSL where a generic key works, no pattern for two fields, no micro-optimisation that hurts reading.

## 5. Output

Match the size of the answer to the question. For "design X" or a new module, give:

1. Assumptions and skipped scope
2. Core requirements
3. Entities and responsibilities (is-a / has-a)
4. API signatures
5. Mermaid `classDiagram`, plus the main call sequence if flow matters
6. Core algorithm and data structures with per-operation cost
7. Patterns used and rejected, with reasons
8. Concurrency and failure plan
9. Code for the critical path in the project's language (stubs for IO)
10. Tests
11. How the next likely requirement slots in

In an existing codebase, follow its conventions and layers first. These rules decide between options; they do not override the house style. For a quick question (which pattern? is this thread-safe?), answer directly: the choice, why, the rejected option, a short sketch.
