# LLD review checklist (run before presenting a design or code)

## Scope
- [ ] Problem restated with a concrete example; assumptions written down.
- [ ] Full requirement list + shortlisted core; skipped items named.
- [ ] Clear which round it is (LLD vs machine coding vs schema) and what the interviewer/user stresses.

## Objects
- [ ] Each class has one responsibility; data lives with the class that owns/validates it.
- [ ] Names say exactly what things are/return.
- [ ] Complex or mutating fields extracted into named classes; no nested maps / parallel maps keyed alike.
- [ ] Relationships justified (is-a vs has-a; composition vs aggregation).
- [ ] No class created "just because"; no redundant state that can be derived.
- [ ] Enums for closed-but-growing sets; value objects immutable where possible.

## APIs
- [ ] Critical API designed first; signatures minimal; return most specific / accept most general.
- [ ] IO returns futures; timeouts considered; specific exceptions.
- [ ] Services are interfaces; dependencies injected (time, data sources, config).
- [ ] No duplicated methods differing only by parameter type.

## Extensibility (OCP/DIP)
- [ ] New variants (rules, strategies, handlers, observers, channels, board types) can be added without editing core classes.
- [ ] Base types only contain behaviour every subtype supports (LSP); capability interfaces split (ISP).
- [ ] Patterns used are justified; patterns considered and rejected are mentioned with reason.
- [ ] Not over-engineered (no config DSL where a generic key works; no premature micro-optimisation).

## Algorithm & data structures
- [ ] Complexity stated per operation; obvious structures checked against every operation.
- [ ] Multiple indexes/composite structures kept in sync on every mutation path.
- [ ] Simple explainable algorithm chosen; optimal alternative mentioned if relevant.

## Concurrency
- [ ] Shared mutable state identified; each hazard has a mechanism (lock / per-key thread / immutability / concurrent collection / client guarantee).
- [ ] Request-handling threads never block on IO.
- [ ] Retries only for retryable errors; DLQ; idempotency; back pressure where push is used.

## Correctness & tests
- [ ] Happy path traced against the example; edge cases listed (empty, ties, limits, duplicates, timeouts, out-of-order events).
- [ ] Tests deterministic (injected clock), one unit at a time, not coupled to changeable algorithms.
- [ ] Validation at entry points (occupied cell, insufficient funds, sum of balances = 0).

## Presentation
- [ ] Class diagram + flow for the main use case.
- [ ] Code for the critical path; stubs for IO.
- [ ] Trade-offs and extensions summarised.
