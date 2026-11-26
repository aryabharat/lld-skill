# LLD workflow: from prompt to tested design

Use this when starting a design task: a new feature, module or service, a change request on existing code, or an LLD / machine-coding / schema round. It gives the order of work, the time budget and what to leave out.

**Contents:** 1 Classify · 2 Clarify and scope · 3 API first · 4 Objects and names · 5 Data structures · 6 Algorithm · 7 Concurrency pass · 8 Tests · 9 Extensions · 10 Change requests on existing code · 11 Interview rounds and time budgets · 12 What to skip · 13 Step card

The yardstick for every step is the same three things: readability, extensibility and correctness. Ask what the next feature will cost to add, not only whether the code works today [L0, L1, L2].

---

## 1. Classify the problem first

The type of problem decides where you start. Name it before anything else.

| Type | Signals | Start from | Key move |
|---|---|---|---|
| **Consumer product** (Splitwise, Zomato, Zerodha, Twitter, Calendar) | Human actors, flows, "design app X" | Use cases per actor, then entities, then APIs | Find the one hard part (debt simplification, recurrence, dispatch, fan-out) and spend the time there [L42, L86, L87, L89, L94] |
| **Engineering component** (cache, event bus, rate limiter, queue, orchestrator, logger) | The customer is another engineer | The API list. Skip use-case diagrams [L90] | Walk CRUD over the core entity to bring out the hidden policies: ordering, consistency, write policy, eviction [L51, L61] |
| **Game / simulation** (tic-tac-toe, chess) | Board, turns, rules, terminal state | The central class (the board), then the move contract [L93] | Pin the inheritance vs composition decision on the whiteboard [L82], then make the terminal check incremental [L93] |
| **Algorithm-first LLD** (Google logger) | Few APIs with tight per-op complexity | Target complexity of each operation, on paper | Combine structures (map + ordered index) [L83] |
| **Schema** (GitHub, BookMyShow, Twitter feed) | "Design the DB schema for X" | Features, then APIs and objects, then tables | Choose the layout from the queries you will actually run [L92] |
| **Refactor / change request** | Existing code plus a new requirement | Tests that pin current behaviour | Smell, then principle, then refactor (section 10) [L0, L82] |

- **Do** confirm the round type (LLD vs HLD vs machine coding) before you design. Assuming the wrong one fails interviews [L82].
- LLD is classes, how they talk and maintainability, not service topology or sharding [L82].

---

## 2. Clarify, state assumptions, list everything, shortlist the core

**When** handed an open prompt -> **Do** write a numbered list of every feature you can think of, then mark the 3-5 you will build and say out loud what you are parking, with a one-line approach for each (for example "activity log = pub-sub on domain events") -> **Because** the full product cannot fit the slot, and naming deferred items shows awareness without spending time on them -> **Flips when** the interviewer or the ticket fixes the scope [L42, L53, L87, L89, L93].

- Ask what is being stressed: the algorithm, concurrency, or extensibility. It decides where the time goes [L50, L83].
- Rank by weight: keep the features that hold the core state model or algorithm, and drop the peripheral ones (comments, notifications, auth, profiles, ratings) [L42, L86, L94].
- Ask what given helpers return and what the API must own (`assignExecutive(orderId)` meant find, choose and persist, not a setter) [L94].
- State simplifying assumptions aloud: single currency, single-threaded access, one node per key, "start arrives before end" [L25, L47, L56, L84].
- For a component, number its engineering requirements and state each policy choice: the read guarantee (for example read-your-own-writes), the write policy, the eviction triggers, the ordering key, what happens on rejection [L51, L52, L53, L71].
- Walk CRUD over the core entity: it removes paths (immutable events have no update/delete) and surfaces replay and ordering [L51, L61].
- Model "mark as done" as a state change or a new record, not as an edit that overwrites history (settle is not edit) [L42, L43].

**Reviewer checks:** explicit core vs deferred list; policy choices written down [L42, L53].

---

## 3. API first: work backwards from the critical method

**When** starting to design or code -> **Do** write the public signatures the caller needs first, then find the one method that delivers the core outcome and write its body top-down as calls to methods that do not exist yet -> **Because** parameters and return types reveal the domain objects, and if time runs out the most valuable part already exists -> **Flips when** the interviewer explicitly asks for the object model first, or the API is fixed by an existing contract [L3, L47, L50, L56].

```java
// Written first. Every type below is discovered from this body.
PaymentGraph getGroupPaymentGraph(String groupId, String userId) {
    BalanceMap total = getGroupBalances(groupId, userId); // auth check + sum
    return expenseService.simplify(total);                // the graded algorithm
}
```

- **Fix the return contract before coding.** Define every input and what each return value means. This is graded as API design [L93].
- **When** an answer has more than two outcomes or carries data (win / draw / in progress, plus the winner) -> **Do** return a small result type, not a boolean [L3].
- Return the type that matches the meaning: a sum of expenses is a `BalanceMap`, not a fake `Expense` [L47].
- **When** a method may do I/O -> **Do** return a future, so the signature itself warns that the call is slow and can fail [L56, L79].
- One public entry point; choose the strategy inside, never `suggestSmartMove` beside `suggestMove` [L11].
- Take server-owned values (market price, `createdAt`) from server state, not from the request [L87, L89].
- Every caller-id parameter must be used for an authorization check in the owning service, before any downstream call [L46, L47].
- Expose user-facing actions only, never internal steps [L87, L90].

**State-first vs behaviour-first (the lessons disagree):** L43 models entities and state first (ER-style) and then checks each API against the model. L47 and L50 say to write the behaviour first and add only the state it needs. **Final position:** in a timed coding round, or any build, start from the critical method and let models fall out of it [L47, L50]. In a discussion-only LLD of a product, listing entities first and then walking every API against them is acceptable [L43, L87]. Either way, every field must have a behaviour that reads it (inferred).

---

## 4. Object discovery and naming

- Nouns in API signatures become classes, one idea each [L3].
- Model the most central class first (board, order, topic) and grow the rest around it. Starting with `User` or `Statistics` over-details the periphery [L93, L50].
- Build an entity-by-behaviour matrix. Behaviours shared by every type go to the base abstraction, and the special ones stay on the concrete class [L82].
- Say the relationship aloud ("a rook is a piece", "a game has a config") and pick the one that reads true. Variation that is really configuration or mode goes in a composed object, not in a fan of subclasses [L21, L82].
- Ask "does this field define the object?" If it does not, and it grows without bound, move it into an association object (`GroupExpenses`) [L43].
- A mutated collection field (watchlist, active orders) earns its own class. Several maps keyed by the same id should become one aggregate class [L87, L90].
- Nested generics (`Map<User, Map<User, Amount>>`) mean a type is missing. Name it [L23, L47].
- Rename as meaning clarifies (`Balance` -> `Amount`); it counts in your favour [L47]. Enum for a set that may grow [L87]; derive computable state instead of storing a flag [L82].
- Inherit from interfaces. Class inheritance is rare and needs a reason [L46].

Interviewers weigh well-named, well-defined objects as the largest part of the evaluation [L46].

---

## 5. Choose data structures from the operations

**When** picking internal structures -> **Do** list every operation, write down what it reads or mutates, and pick the cheapest structure for that access pattern. Then report the cost of the worst API -> **Because** a design is judged by its worst operation [L70].

| Access need | Structure | Ref |
|---|---|---|
| Exact-key lookup | Hash map (concurrent variant under threads) | [L70] |
| "First after T", range, nearest | Sorted map with floor/ceiling (Java: `ConcurrentSkipListMap`) | [L67, L70] |
| Lookup by id **and** retrieval in another order | Two indexes over the same object (map + heap/TreeMap) | [L83] |
| Two independent eviction orders (TTL and LRU/LFU) | One index per ordering | [L56, L57] |
| Frequent update by key | Map, not list scan | [L87] |
| Append-only, time-ordered list | Binary search on the timestamp | [L89] |

- Sort on the key you need (start time), not the natural key (id) [L83]. Route every mutation of multi-structure state through one internal method [L58, L68].

---

## 6. Algorithm: first cut, then optimal

- Fix per-operation complexity on paper first [L83]. Ship the simplest valid version (first empty cell) to unblock the end-to-end flow, then improve [L6].
- **When** a state change is local -> **Do** check only what that change can affect (only the mover can win, only through the placed cell), then keep running aggregates if O(1) is asked for [L93].
- **When** the exact answer is exponential -> **Do** ship a bounded heuristic (greedy two-heap settlement), state where it fails with a counterexample, and name the exact route (subset sum) without coding it [L44, L48].
- Do not spend the round on algorithm brilliance where the course does not (a win-then-block heuristic is enough, so skip minimax) [L11].

---

## 7. The concurrency pass

Run this pass after the model and the algorithm exist. In a 1-hour LLD round, **name** the risks and the fixes. In machine coding, **implement** them [L85].

1. **Find the shared mutable state.** A table read on every request and updated now and then, balances that must sum to zero, a map plus an index [L45, L84, L85].
2. **Ask which need it is:** exclusivity (locks) or ordering (route each key to one thread) [L84].
3. **Pick a mechanism:**
   - Multi-field invariant with concurrent readers: build a new immutable snapshot and swap the reference. Stale but valid beats torn [L45].
   - Per-entity ordering with parallelism across entities: hash(key) mod N onto single-threaded executors [L55, L63, L65, L84].
   - A composite structure: one lock over the whole object. Swapping each part for its concurrent version does not make the combination safe [L84].
   - Many callers sharing one expensive client: an object pool [L94].
4. **Keep I/O off request threads.** Return futures and run continuations on a named executor [L54, L75, L79].
5. **Keep concurrency out of the core flow when the business allows** (sequential courier offers) [L94].

Seniors must at least discuss mechanisms and how to test them; "ConcurrentHashMap and synchronized" is not an answer [L84]. **Disagreement:** L85 says a 1-hour LLD rarely goes into locking. L84 and L94 show interviewers probing concurrency anyway, and L85's own student noted it is gaining weight. **Final position:** always name the concurrency points, and code them when the round allows.

---

## 8. Tests

- The worked example you drew on the whiteboard is your test oracle. Turn it into the first test [L49].
- Order: happy path first, then edge rules (timeouts, terminal state, illegal moves) [L36, L49].
- Inject the clock, and pass time in explicitly [L35, L64, L83].
- Test rules apart from heuristics, scripted so outcomes are deterministic; one unit per test [L10, L13, L37].
- Debug in passes: nulls (audit every write site), then interactions between structures, then concurrency [L69].
- Concurrency tests need scheduling: a contract-respecting client firing thousands of interleaved calls, with the output order asserted [L84].
- Final pass: walk each path (get-hit, get-expired, get-miss, set-new, set-existing) against every structure, and make sure it compiles [L58, L81].
- Even in 45 minutes, state a test plan; skipping it was marked down [L94].

**In a codebase:** correctness before extensibility: tests pass first, then refactor [L37].

---

## 9. Extensions

- Leave clear extension points (strategy for a policy, a rule list, a callback) but build only one or two variants [L61, L64, L78].
- Cross-cutting consumers (activity log, notifications) go behind domain events or Observer, added after the core [L41, L42, L94]. Use Observer only when subscribers vary at runtime, not for one fixed recipient [L87].
- Expect a mid-round twist (timers, forks, undo); absorb it without editing the core [L17, L21, L29].

---

## 10. Change requests on existing code (the course's loop)

The game-engine series runs one loop: a feature request breaks the naive code, and a principle is pulled in only then [L0, L14].

1. **Pin behaviour.** If the class has no callers or tests, write a test around its public methods first. The test is its first caller [L33, L82].
2. **Run it and make it correct** before critiquing the design [L7, L37].
3. **Find the smell.** List *where* the code can improve (duplication, coupling, file layout, `instanceof` chains, growing if-chains, nested generics, parallel maps) before deciding *how* [L4, L18, L23, L90]. Start with the dirtiest code [L82].
4. **Find the right home for new state.** Walk every existing class as a candidate home and reject each one with a reason before you create a new collaborator [L21, L22].
5. **Name the principle the pain points to,** then check that the pattern's shape actually fits. State was rejected because the "states" had no real transitions. A rule engine was rejected because the checks depended on order [L22, L32].
6. **Refactor in small steps behind the stable public API,** and rerun the tests [L11, L22, L9].
7. **Judge the result** on readability, extensibility and correctness, not line count. Revert the parts that cost more than they paid back, rank the remaining refactors by payoff over effort, and say which smell you are leaving and why [L16, L23, L31]. Code that gets shorter after a refactor is evidence it was right [L59]. Delete a pattern that no longer earns its place [L41].

**Reviewer checks:** feature arrives as an addition, not an edit to tested core; a regression test exists; any pattern answers a real change [L1, L32, L89].

---

## 11. Interview rounds and time budgets

| Round | Length | Expected output | Ref |
|---|---|---|---|
| LLD discussion | ~45-60 min | Requirements, classes, signatures, call flow, maybe one method coded; name the concurrency risks | [L85, L87] |
| Machine coding | ~2-3 h | Compiling, running code for the core, tests, concurrency in code | [L53, L83, L84, L87] |
| Schema | in senior and manager loops | Features, access patterns, normalized tables, depth on 1-2 hard parts | [L92] |

**Budgets the course gives (they vary; treat them as ranges):**
- **45 min:** cover 3-4 core features and explicitly park the rest. Still write the core loop and state a test plan [L90, L94].
- **60 min:** about 35 min on the board (requirements, objects, APIs, caching and concurrency), about 25 min coding the critical path and a test [L45]. L50 gives 25-30 min of discussion. Requirements alone take 5-10 min [L87].
- **90 min (chess stream):** about a third on thinking and drawing. Classes and the inheritance decision were settled about 25 min in [L82].
- **2 h+ machine coding:** the skeleton took about 10 min, the core algorithm a few minutes once the APIs existed, and tests the final stretch [L47, L48, L49]. Get a runnable main early, then iterate [L6].

**Interview-only habits:** narrate while coding [L93]; know your editor's shortcuts (Google often uses a plain doc) [L50, L83]; ask before using AI/IDE help [L75]; keep diagrams clean; if you do not know the domain's rules, ask or swap the problem [L82].

---

## 12. What to deliberately skip (and say so)

| Skip | Say instead | Ref |
|---|---|---|
| Plain CRUD (getUser, getGroup), registration, auth plumbing | "Trivial, assumed" | [L45, L46, L50] |
| DB, network, connectors, DTO boilerplate | Mock with in-memory maps; "assume a SQL/JSON library and DI" | [L47, L56, L76] |
| Building a cache inside a full-system LLD | Name what to cache and its consistency | [L45] |
| Exact exponential algorithms, diff algorithms nobody asked for | Name them, ship the heuristic | [L44, L92] |
| Peripheral rule complexity (castling, full check detection) | Named stub, agreed with the interviewer | [L82] |
| Many retry policies or config menus | "Configurable; one or two implemented" | [L61, L74] |
| Hand-written singletons and library internals | "From a DI container or library" | [L25, L67] |

Do not skip: the core method, its contract, one test, the authorization check on caller-scoped APIs, and naming the concurrency risks [L46, L47, L94].

---

## 13. Step card

```
0 CLASSIFY   product | component | game | algo-first | schema | refactor; confirm LLD/MC/HLD
1 SCOPE      list all features -> mark 3-5 core -> park rest aloud (1-line approach each)
             ask what is stressed; state assumptions; for components: CRUD walk + policies
2 API        public signatures; pick the ONE critical method; fix its return contract;
             futures for I/O; caller id -> auth check first
3 BACKWARDS  write critical method top-down; models fall out of its body
4 OBJECTS    central class first; is-a vs has-a aloud; field must define the object;
             nested generics -> named type; enums; derive, don't store
5 STRUCTURES op -> access pattern -> structure; two indexes if two orders; worst-API cost
6 ALGORITHM  complexity on paper; simple correct first; incremental check; heuristic + its limits
7 CONCURRENCY shared mutable state? exclusivity vs ordering; snapshot swap | key-striped
             executor | one lock over composite | pool; I/O off request threads
             (1h LLD: name it; MC: code it)
8 TESTS      whiteboard example = oracle; happy path then edges; inject clock;
             nulls -> interactions -> concurrency; walk every path; compiles
9 EXTEND     strategy/rules/events as seams; build 1-2; list next steps
CHANGE REQ   pin tests -> make correct -> smell -> right home -> principle (check fit)
             -> small refactor behind stable API -> judge, revert what didn't pay
TIME 60m     ~35 board / ~25 code+test   45m: 3-4 features + test plan   MC: run early
```
