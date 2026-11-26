# Testing designs and code

Use this when writing the first runnable code for a design, adding tests before a refactor, debugging a failing or suspiciously green test, testing time- or concurrency-dependent components, or deciding how much to test in a timed machine-coding round.

**Contents:** 1. Build order · 2. Shaping a test · 3. Determinism · 4. One unit per test · 5. Tests that survive change · 6. Tests as a refactoring and debugging tool · 7. Example-driven tests · 8. Bug passes and concurrency tests · 9. Timed round vs production · 10. Checklist

---

## 1. Build order: run it before you critique it

| When | Do | Because | Flips when |
|---|---|---|---|
| Several classes exist but nothing drives them | Write a thin driver (`main` or one test) using only the public API | Correctness before critique; the first run found an NPE, a false game-over on an empty board and missed wins [L6, L7] | A test harness already drives the flow; the test is the driver (inferred) |
| A "smart" collaborator (AI, pricing, ranking) is not designed yet | Ship the trivial valid version (first empty cell) behind its own method | Unblocks the end-to-end flow and leaves a seam for the real strategy [L6] | The trivial stub hides behaviour you need to test (inferred) |
| Code is correct but each fix added a nested branch | Stop patching; plan a refactor, under tests | Hot-fix accretion gives code that works now and resists the next change [L7] | - |
| A test fails or passes wrongly and you are tempted to redesign | Fix correctness first, against the expected state, then refactor | Refactoring broken code has no value; refactor only once it is correct and covered [L37] | - |

Production: the walking skeleton. Reviewers ask whether a runnable path existed before abstractions were polished.

## 2. Shaping a test

- **Name suites by behaviour or flow** (`GamePlayTest`, `CheckoutFlowTest`), not by internal class, when several classes collaborate to produce the behaviour. Use `<Class>Test` only when truly testing one class alone. [L9]
- **Scripted inputs, not interactive ones.** Replace Scanner/stdin with a data structure (array of moves plus an index). Prioritise scenarios that are tedious by hand: full draws, opponent wins, every win line. [L9]
- **Assert, never print-and-eyeball.** Printing is for debugging; convert to assertions once the run passes. Have APIs return values (strings, results) so tests can assert on them. [L9, L49, L84]
- **Fresh-per-test setup hook** (`@BeforeEach`); extract the duplicated driving loop into a helper so each test is data plus assertions. [L9]
- **Write one test, run it, then the next.** The first run found an index bug before more tests piled on. [L9]
- **Readable fixtures:** cells named `c00, c01`; a board-builder fixture. [L36, L37]
- **Assert the contract, not incidental order.** Compare graph/set results (payment edges) as maps or sets; HashMap or heap tie-breaking makes ordered assertions flaky. [L49]
- **Check identity of the right thing:** assert the delivered event id, not just non-null; compare domain values with `equals`, not `==` (a winner assertion failed purely on reference equality). [L36, L69]

```java
class GamePlayTest {
  @BeforeEach void setup() { rules = new RuleEngine(); game = new GameEngine(rules); }
  @Test void columnWin() {
    var r = play(new int[][]{{0,0},{1,0},{2,0}}, new int[][]{{0,1},{0,2},{1,1}});
    assertTrue(r.isOver()); assertEquals("X", r.winner());
  }
}
```

## 3. Determinism: inject what varies

| Source of nondeterminism | Do | Refs |
|---|---|---|
| Wall clock | Pass timestamps or durations as parameters, or inject a `Clock`/`Timer` (singleton in prod, fake or subclass in tests). Never `System.currentTimeMillis()` in domain or test code; runs gave 3 ms then 5 ms | [L33, L35, L36, L64, L69, L83] |
| Sleeping | Fake timer, never `Thread.sleep` in unit tests | [L36, L64] |
| Same instant stamped into several structures | Read the clock once into a local | [L57, L83] |
| Evolving algorithm (AI, strategy, ranking, ML scorer) | Script every actor's inputs in rule tests, or inject a deterministic fake behind the strategy interface | [L10, L13] |
| External systems (DB, remote cache, CRUD services) | In-memory maps or stubs; plain unit tests suffice for an in-process monolith with no collaborators | [L8, L46, L47, L56] |

**Pick numbers you can do by hand** and state the arithmetic in a comment: budget 11 s, 5 s moves (X 11 -> 6 -> 1, O 11 -> 6), then O spends 7 s against 6 s left, so X wins. Keep non-boundary tests off the boundary (it blurs `<` vs `<=`); test the limit, just under and just over separately. [L33, L36, L37]

**Units:** config in seconds and timestamps in ms made every limit 1000x too small. Name units (`maxMoveMs`) or use `Duration` (inferred from the bug). [L37, L57]

Flips when: you are testing the clock integration itself (inferred) [L36].

## 4. Test one unit at a time

- **When** one test exercises a factory and the object it builds, **do** split it: test the factory's output field by field (including "feature disabled means null"), then the logic with a known-good config. **Because** a factory bug (per-move limit set to the total budget) surfaced as a game-logic failure and was hard to localise. Catching two bugs in one test feels efficient but is an anti-pattern. [L37]
- Unit-test value objects on their own: a broken `Amount.add` silently corrupts every total built on it. [L49]
- Pull threading or nested-map behaviour into its own class (`KeyedExecutor`, a subscriber-index wrapper) so it can be tested without poking at internals. [L65, L68]
- Separate correctness tests (rules, deterministic, scripted) from strategy-quality tests (tolerant, property-style: "always returns a legal move"). Never feed a heuristic's output into a correctness test. [L10, L13]

## 5. Tests that survive change

Judge tests on extensibility, not only readability and pass/fail. [L10]

- **Smell:** scripted moves for one side while a live AI plays the other. A changed AI makes a scripted move illegal or blocks the asserted win. Red CI after an algorithm improvement usually means this coupling. [L10]
- **Fix:** assert the rule engine's verdict on a board you build directly, or script both players. [L10, L13]
- **Course position changed:** L9 called AI-driven gameplay tests progress; L10 calls them bad code; L13 scripts both players. Final position: script both.
- **When adding validation breaks many tests, fix the tests, not the validation.** Once `setCell` refused occupied cells, the old tests failed: they had been passing on impossible games. Rejected: loosening the invariant, rewriting assertions to match current output, or making `setCell` idempotent to silence a double move. [L13, L37]
- **Long, repeated setup is a production design signal:** fix creation (factory overloads, `addExpense` instead of a prebuilt constructor map, maps keyed by user ID not `User`) rather than adding test-only helpers. [L34, L35, L49]

## 6. Tests as a refactoring and debugging tool

**Before changing code nobody calls, write its first caller.** Test the behaviour behind each public method, plus characterization tests for each existing branch. Reading the surface to decide what to test is what exposed duplicated branches in `move`. [L32, L33]

Run tests before and after every refactor and expect identical results; score refactors on correctness, readability and extensibility, never lines saved. Re-check IDE extractions: one wired in the wrong variable. [L16, L33]

**Distrust greens.**
- A test that passes first time: re-derive the expected outcome. A per-move timeout test passed while the arithmetic said the player must lose; later moves were overwriting the result because `move` had no terminal-state guard. [L36]
- A substantive behaviour change with every test still green: the tests are not exercising it, or it is broken. [L12]

**Debug bottom-up, layer by layer.** When output is wrong, assert the lowest layer first, then the aggregation on top. Splitwise group balances came out as +90, +10, -90 instead of 50, 30, -80. Per-expense balances were correct, so the fault was in aggregation: `Amount.add` returned its argument instead of a sum. Symptom-to-cause mapping: totals equal to the last input mean an accumulator that overwrites (inferred). [L49]

```java
// bug: Amount add(Amount o) { return o; }
Amount add(Amount o) { return new Amount(currency, value + o.value); }
```

Inspect real state (debugger, readable `toString`) before touching logic; do not guess. Put context (board, row, col) in exception messages. [L7, L13, L36]

## 7. Turn whiteboard examples into exact-number tests

- The worked example drawn during design is the test oracle: already verified, and it keeps code aligned with the agreed design. [L49]
- Splitwise: three expenses in group "123" give A 50, B 30, C -80. Payment graph for A +90, D +80, F +40, E -100, B -70, C -40 gives four payer->payee edges (E->A 90, B->D 70, C->F 40, E->D 10), asserted as a map. [L49]
- Logger: P3 starts 7 and ends 19, P2 8-12, P1 12-15; poll order P3, P2, P1 (P2 finished first but waits); a fake clock makes these exact-string assertions. [L83]
- Event bus default contract: event published before subscribe is not delivered; one published after is delivered with the right id. [L69]
- Production additions: applying the payment graph zeroes every balance with at most n-1 edges [L48]; a known non-optimal fixture documenting a heuristic [L44]; the O(1) win check equals a brute-force scan on random games (inferred) [L93].

## 8. Bug passes and concurrency tests

**Fix in three ordered passes:** nulls/empty values, then interactions between internal structures, then concurrency. Each class masks the next; you cannot reason about races while NPEs abort the flow. [L69]

- **Null pass:** list every internal data structure; for each, where is it written and can a missing entry be read? Strike constructor-only fields. Exhaustive, unlike chasing one stack trace at a time. Fixes: `getOrDefault` on reads, `computeIfAbsent` on writes, per-entity state initialised at creation, sentinels where concurrent maps forbid null, explicit `-1` for "not ended". [L69, L83]
- **Interaction pass:** is each structure updated everywhere it must be (both indexes on remove)? Do dependent conditions apply their side effect once? Removing the NPEs did not make the event-bus test meaningful; the cursor semantics were wrong. [L37, L69, L83]
- **Terminal paths:** every row, column, both diagonals, draw, empty board, moves after game over. [L7, L36, L93]

**Concurrency tests need scheduling, not just method calls.** Build a test client that obeys the real client contract (no `end` before its `start`; earlier starts begin before later ends), fire many randomly interleaved commands through a large pool (lesson: 1000 tasks, 5000-thread pool), and assert global output order. Rerun with inverted start times to catch ordering assumptions. Without the lock plus key-striped executors, output came out of order. Run repeatedly; blocking waits need timeouts so a bug fails instead of hanging. [L84] Other targets: read-your-writes on one key across threads, one backend call for N concurrent gets (request collapsing), same-key order preserved. [L52, L55, L59, L62]

## 9. What to test: timed round vs production

### Interview (timed round)
- Order: objects and behaviours, core algorithm, then tests. Test the core algorithm's output; it forces every object on its path to exist. Testing is roughly the last 6 minutes of a Splitwise-sized round. [L45, L46, L49]
- Happy paths of the core algorithm first; name edge cases, refactors and concurrency tests as follow-ups. [L49, L83]
- Mock storage and trivial CRUD; say so out loud. [L46, L47, L56]
- Positive signals: assertion tests instead of an interactive `main`, removing wall-clock dependence unprompted, a stated "nulls, interactions, concurrency" plan. Common failure: never running the code. [L9, L35, L49, L69]
- Seniors must at least describe how they would test concurrent code. [L83, L84]

### Production
Everything in sections 3-8, plus: every requirement has at least one test [L53]; boundary tests at limit, limit - 1 and limit + 1 [L37]; the randomised concurrency harness runs in CI [L84].

## 10. Checklist

- [ ] A runnable end-to-end driver or test existed before refactoring or critique.
- [ ] Suites are named by behaviour; setup is fresh per test; driving loops are helpers.
- [ ] Inputs are scripted; outcomes are asserted, not printed.
- [ ] No system clock or sleep in logic or tests; time is injected; expected values are hand-computable.
- [ ] No test depends on the choices of an AI, strategy or other evolving algorithm.
- [ ] Each test covers one unit; factories and value objects are tested separately.
- [ ] Whiteboard examples exist as exact-number tests; unordered results asserted without order.
- [ ] First-run greens and "change with no red" were re-checked.
- [ ] Failures were debugged bottom-up, lowest layer first.
- [ ] Null, interaction and concurrency passes done, in that order.
- [ ] Concurrent code has a randomised-interleaving test asserting order or invariants, with timeouts.
- [ ] All terminal paths, the empty state and boundary values are covered.
