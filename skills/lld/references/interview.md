# LLD interview guide

Use this when preparing for, running, or grading an LLD or machine-coding interview: picking a time plan, anticipating probes, judging an answer, or giving mock-interview feedback. For the design content itself, use the topic references; this file covers how the round is played and scored.

Contents: Round types · Time budgets · What interviewers push on · Strong vs weak answers · Unknown domain rules · Drawing and communication · Mock rubric and feedback · Probe bank per case study

## Round types

| Round | Typical length | What it probes | What you deliver |
|---|---|---|---|
| **LLD discussion** ("design Zomato/Zerodha") | 45-60 min | Requirements, object model, relationships you can defend aloud, method signatures and call flow, product judgment | Class diagram, signatures with return types, one core method implemented at most; running code is not expected [L87, L94] |
| **Machine coding** (cache, event bus, rate limiter, load balancer) | 2-3 h | Hands-on coding of a concrete engineering component: real algorithms, concurrency, extensibility, testability | Compiling code, working happy path, tests [L53, L82, L83, L90] |
| **Algorithmic LLD in a plain editor** (Google logger) | ~45-60 min | Picking data structures to hit target complexity, then concurrency talk | Compact readable code with no IDE [L83] |
| **DB schema round** (senior/manager loops, after system design) | ~45-60 min | Access patterns, normalisation of memberships, authz vs authn, depth on one hard part | Tables, keys, indexes tied to named queries [L92] |

- LLD is not HLD: it is about how classes talk and whether code would survive a pull request, not service topology, sharding or tech stack. "Efficiency" here means object counts and hidden network calls [L82].
- Do not assume the round type; confirm it. A reported "LLD" round was judged machine coding by the instructor [L82, L85].
- Seniority sets the bar: freshers are expected to clear the algorithmic core (logger part 1); SDE2 adds requirements, behaviours, state and algorithm; SDE2/3 and seniors must at least discuss concurrency, blocking and how to test concurrent code even if not coding it [L83, L84]. Junior prompts are whole products ("design Cricbuzz"); senior prompts narrow to a component ("the real-time notification part") [L88]. Some algorithm helps especially for senior roles [L86].
- Language is free. Ask before using AI assistants or IDE help; allowed in the course, not everywhere [L75, L82].

## Time budgets

| Phase | 1-hour LLD | 2-3 h machine coding |
|---|---|---|
| Requirements and scope | 5-7 min, cap at 10 [L87] | 10-15 min, numbered list, mark what you will build [L53] |
| Entities, behaviours, diagram, core algorithm on board | to ~25-35 min total [L45, L50, L82] | about a third of the session [L82] |
| Core code | ~25 min [L45] | the bulk; core method first, wrappers last [L47] |
| Tests and walk-through | last ~6 min [L49] | runnable tests early, concurrency tests last [L69] |

Reference timings from the course: Splitwise service skeleton ~10 min [L47]; heap settlement ~4 min once balances exist [L48]; keyed executor ~6 min [L65]; rate-limiter client ~10 min with IO stubbed [L77]; hot loading ~1 min once a single insert choke point exists [L59]. In 45 min, cover 3-4 core features and park the rest by name [L90]. Fix your own time box at the start and say it [L89]. Before handing in, make sure it compiles [L81].

## What interviewers push on

| Push | What they want to see | Refs |
|---|---|---|
| **Naming** | Domain names that read without explanation; renaming live (`Balance` to `Amount`) counts in your favour | L46, L47 |
| **SRP / placement** | Why each method lives where it does; win detection belongs to neither the AI nor the engine; no `GameManager` | L5, L8, L10 |
| **A new requirement mid-problem** (forks, timers, undo, email, new AI) | The design absorbs it by adding a collaborator or config object, core class untouched, client API unchanged | L17, L21, L22, L29, L39 |
| **Pattern fit** | Pattern arises from a need; can tell State from Strategy; can reject a pattern with reasons; not every refactor is a pattern | L13, L32, L87, L89 |
| **Concurrency** | A concrete race (torn read across the zero-sum invariant, start/end race), exclusivity vs ordering, key-to-thread routing, which thread you block, pooling a shared expensive resource | L45, L55, L62, L79, L84, L94 |
| **Testing** | Assertion-based tests, injected clock, tests that catch your own bugs, a test plan for timeouts and fallthrough | L9, L35, L37, L49, L94 |
| **Complexity** | Per-API complexity table, why each structure fails alone, honest optimality claims | L44, L70, L83, L93 |

## Strong vs weak answers

| Strong | Weak |
|---|---|
| Lists many features, picks a subset, names a one-line approach for deferred ones (pub-sub for comments) [L42, L93] | Dives into comments, auth, registration or user CRUD first [L42, L50] |
| Asks what is being stressed (algorithm vs concurrency) and builds the central difficulty first [L50] | Writes many model classes with guessed fields before any behaviour [L50] |
| Starts the diagram from the central entity (board) [L93] | Details `User`/`Statistics` while `Board` is undefined [L93] |
| Fixes the core method's contract before coding, and explains why a boolean is not enough [L3, L93] | Ambiguous return values discovered mid-code [L93] |
| States the strategic decision for the problem and justifies it (chess: inheritance vs composition; Splitwise: the balancing algorithm) [L82] | Forces inheritance early, adds type switches [L82] |
| Shows the naive version, names its scaling problem, then refactors (rule engine, chain) [L17, L24] | One big method with nested ifs, or fallbacks via helpers calling helpers [L24] |
| Volunteers limits: greedy settlement is not optimal, global rate limit is approximate [L44, L72] | Claims optimality or "the cache is consistent" without defining it [L44, L52] |
| Precise guarantees: names the anomaly, the routing key, and what interleavings remain [L52, L62] | "Use ConcurrentHashMap and synchronized" as the whole answer [L84] |
| Runs code early and debugs layer by layer; prints become asserts [L6, L49] | Never runs anything; polishes abstractions [L6, L69] |
| Says which smell is being left and why [L31] | Pretends the code is clean |

## Unknown domain rules

- Rules of chess (or any game/domain) are not what is tested. Ask the interviewer, or ask to switch problems [L82].
- Stub the complex, peripheral rules (castling, full check detection) under a clear name and confirm they are out of scope; they grade decomposition, not rule completeness [L82].
- Ask what given helpers return and what the API must own (Zomato: helper gives top-10 nearby executives sorted by ETA; the API must select and persist) [L94].
- Walking a real product's flow (opening the app at checkout) to collect requirements is acceptable [L91].
- When a business fact changes the design, ask it directly (employees vs gig workers decides sequential vs broadcast offers) [L94].

## Drawing and communication

- Think and draw before coding: entities, then behaviours, then split common vs special behaviours; common ones become the shared abstraction [L82].
- Say relationships aloud in plain language ("a rook is a piece", "an order has a log"); the sentence that reads true picks inheritance or composition [L82].
- The class diagram is your aid, but every decision on it should be spoken [L87]. Keep it light; spend the time on the core method [L93]. Sloppy diagrams count against you [L82].
- Before code, a short call-flow or component diagram; keep glancing back at it and at the agreed example while coding [L46, L50].
- Narrate while coding [L93]. State simplifying assumptions out loud (single-threaded access, one node per key) instead of silently relying on them [L25, L56].
- Admit shortcuts as shortcuts (generic exceptions, stubbed transport, assumed JSON/SQL library) [L76, L79].
- Catching and fixing your own bugs on camera is part of the signal; trace loops aloud [L57, L80].
- Revisiting and simplifying an earlier decision is valued [L27]; formatting is judged too [L50].

## Mock rubric and feedback

Modelled on the Zomato mock (45 min, outcome between hire and strong hire) and the tic-tac-toe walkthrough [L93, L94].

### Rubric

Score each 1-4 (1 missing, 2 partial, 3 solid, 4 strong):

| Dimension | 4 looks like | Source |
|---|---|---|
| Requirements and scope | Listed features, chose a subset, parked the rest by name, asked what helpers return | L93, L94 |
| Object model | Central entity first, cell richness proportional to domain, one status plus a log, no duplicated state machines | L93, L94 |
| API contract | Signatures and return codes fixed first; "assign" owns find, select, persist | L93, L94 |
| Product judgment | Decisions tied to business facts (sequential vs broadcast; late assignment off the checkout path) | L94 |
| Core algorithm | Correct, with complexity; reaches the follow-up (O(n) through the move, then O(1) line sums) | L93 |
| Patterns and extensibility | Pattern named and its shape shown; new consumer needs no edit to existing code | L94 |
| Concurrency and resources | Parallel across entities, sequential within one; pooled expensive clients | L94 |
| Code | Enough real code for the core loop, readable names, merged duplicate loops | L93, L94 |
| Testing | Concrete plan: fakes, fake clock, fallthrough, explicit failure, illegal moves | L93, L94 |
| Communication | Narrated, assumptions stated, accepted correction gracefully | L93, L94 |

Outcome mapping (inferred): mostly 4s with no 1s = strong hire; mostly 3s = hire; any 1 on algorithm, code or correctness = lean no. Zomato scored high on judgment and patterns, low on code and testing, landing between hire and strong hire [L94]. Most tic-tac-toe candidates reach O(n); O(1) separates the top [L93].

### Feedback format

1. **Outcome**: one line (e.g. "between hire and strong hire").
2. **Strongest positives** (2-3, specific): the decision and why it was good. Zomato: argued sequential offers for employed riders; argued assignment can wait while food cooks, and the interviewer retracted his own objection; showed an Observer diagram [L94].
3. **Gaps** (2-3) with the fix: "not enough code; reserve 15 min for the core loop", "no testing discussion; name the fakes and cases even in 45 min" [L94].
4. **Missed probes**: what the interviewer was steering toward (resource contention, where the expected answer was an object pool, not semaphores or a plain queue) [L94].
5. **Next drill**: one concrete exercise.

## Probe bank per case study

Follow-ups once the base design stands; expected direction in brackets.

**Tic-tac-toe** [L3, L12, L17, L21, L29, L93]
- Make `makeMove` and `getWinner` O(1) on n x n. (per-row/col sums, two diagonals, abs == n)
- Add undo. (move log; invert or replay)
- Add timed games, per-move and per-game. (config object, not `TimedGame extends Game`)
- AI must look ahead. (copy vs undo; concurrency)
- Detect forks. (rules component, not AI; pluggable rules)

**Chess** [L82]
- Inheritance or composition for pieces? (say is-a aloud)
- Does this move expose my own king? (simulate on a copy)
- Has the pawn moved? (derive from rank, no flag)
- Should the board be a singleton? (no: temp boards and multiple games)

**Splitwise** [L43, L44, L45, L46]
- Settle vs delete an expense. (state change, keep history)
- Minimise transactions. (net balances, two heaps, n-1 bound, greedy not optimal)
- Reader sees half an update. (immutable swap or read/write lock)
- What to cache? (expensive group reads)
- Who may view a group? (caller id, membership check first)

**Cache** [L51, L52, L54, L55, L57, L59]
- Write-through or write-back? (state risk of loss)
- Read your own writes while DB write is in flight. (per-key blocking, FIFO)
- Ten clients miss the same key. (request collapsing)
- LRU plus LFU plus TTL. (one index per ordering)
- Slow region delays fast one. (async futures, separate executor)

**Event bus / message queue** [L61, L62, L63, L67, L68, L90]
- What exactly is ordered? (scope, routing key)
- Subscriber wants events after time T. (sorted concurrent map, strictly after)
- Retries exhausted. (DLQ, not log-and-drop)
- Where do offsets live? (broker, with reset for replay)
- Is push an API? (no, internal side effect of publish)

**Rate limiter** [L71, L72, L74, L79, L80, L81]
- Network call per request? (no: local decision, batched sync)
- Limiter unreachable. (fail open by default)
- Constructor needs remote config. (inject resolved, no blocking)
- Adaptive threshold after many accepts. (simulate; clamp)
- Sliding-window memory. (evict head before deciding)

**Logger (Google)** [L83, L84]
- Target complexity for start, end, poll. (map + heap/TreeMap)
- End arrives before start. (contract or buffer)
- Never-ended head blocks poll. (expiry)
- Test concurrency. (random valid interleavings, assert returns)

**Orchestration service** [L85]
- Call order from dependencies. (topological sort, cycle check)
- Routing table updated at runtime. (snapshot per request)

**Calendar** [L86]
- Recurring events storage. (rules, not rows)
- Edit "this and following". (end + clone)
- ID generation. (collisions vs idempotency)

**Zerodha** [L87]
- Why interfaces? (loose coupling, v2 service)
- Polling vs push for order status. (Observer/SSE)
- Price from request? (no, server state)

**Twitter trending** [L89]
- Celebrity fan-out. (pull on read)
- "New since last visit". (stored lastSeen, indexed lookup)
- Is this refactor a factory? (no, plain inheritance)

**Coupon engine** [L91]
- New condition type. (Rule object, no engine edit)
- Per-user usage limit. (per-(coupon, user) record)
- Clubbing coupons; tax base. (explicit merge rules; tax after discount)

**DB schema / Git** [L92]
- Repo members. (junction table)
- Store file history. (content-addressed blobs)
- One query per tree level acceptable? (only if not hot)

**Zomato** [L94]
- Does `assignDeliveryExecutive` take the executive? (no, it finds and persists)
- Broadcast or sequential? (depends on whether workers can decline)
- Assign at order time? (no, defer while cooking)
- Orders in many cities at once sharing a notifier. (parallel per order, object pool)
- Payment must react to cancellation. (Observer, no Order edit)
