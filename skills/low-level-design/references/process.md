# LLD / machine-coding process (as taught across the course)

## 0. Know which round you're in
- **LLD round** (~45-60 min): requirements, objects, class diagram, APIs, flow, 1-2 key methods, mention concurrency/tests. Running code not expected.
- **Machine coding** (2-3 h or take-home): working code, tests, concurrency handled, clean packages. Many companies *call* this "LLD" - ask.
- **Not HLD**: LLD is about code quality and object interactions, not service topology or scale. Database schema is usually secondary (but senior/manager rounds at ServiceNow/Oracle/Salesforce did ask schema in depth).
- Level expectations: freshers - solve the algorithmic core; SDE2/3 - also consider blocking, concurrency, tests, extensibility and propose standard solutions; seniors - often one component in depth.

## 1. Clarify (5-10 min)
- Restate the problem with a **concrete example** (6 friends splitting a bill; crypto app's websocket; Zomato checkout screen). Examples reveal objects and edge cases, and become your test data.
- Ask: which parts matter most to the interviewer - algorithm? concurrency? extensibility? API design?
- Ask feature questions that change the design (tic-tac-toe: timed? undo? spectators? stats/ELO? tournaments? AI?).
- State assumptions out loud ("start always reaches us before end for the same process"; "all requests for a key land on one node").

## 2. List requirements, then shortlist
- Brainstorm actors and use cases (use-case diagram for consumer products): User vs System responsibilities.
- Write the whole list, then pick 3-6 core features with the interviewer. Explicitly park: auth/KYC, payments, notifications internals, CRUD getters, comments, activity log, recommendations, analytics.
- Number requirements so you can refer back (cache: 1 read-your-writes, 2 write policies, 3 TTL, 4 eviction LRU/LFU, 6 request collapsing, 7 hot loading, 8 event logging).

## 3. Choose the starting point
- Consumer product: entities from the use cases.
- Engineering product: **API first** (`get/set`, `publish/subscribe/poll`, `shouldAccept`, `start/end/poll`), then classes.
- Game: the most important class (Board) first - small classes first leads to over-detailing them.
- Behaviour-driven vs state-driven: think about state (ER-like) to discover objects; code **behaviour-first** from the critical API backwards so you only build what's needed.

## 4. Define objects (biggest chunk of the interview)
- For each entity: fields (state) and behaviours; who owns which data (SRP).
- Name precisely; names must not lie about return types/meaning.
- Relationships: is-a (inheritance) vs has-a (composition: part can't exist without whole - User/Portfolio; aggregation: part can exist independently). Say which and why.
- Extract complex/mutating fields into their own classes (Watchlist, ActiveOrders, PortfolioStock, BalanceMap, RuleSet, Topic).
- Enums for closed sets that may grow (OrderType MARKET/LIMIT/GTT, OrderState); boolean only for truly binary.
- Store ids rather than full objects where they'd bloat caches (Group holds userIds); in pure in-memory LLD, object references are fine.
- Derived values (current portfolio value, P&L, game info derivable from board) are computed, not stored, unless needed for speed.
- Use wrapper/value types for ids (`Topic`, `EventId`, `EntityId`) when many maps are keyed by strings - compiler catches mix-ups.

## 5. Define APIs / services
- Service per responsibility (UserService, StockService, OrderService, NotificationService, ValidationEngine; GameEngine vs RuleEngine vs AIEngine).
- Services as **interfaces** + implementations (multiple implementations; versioning; dependency inversion).
- Signatures: minimal parameters (crunch them: pass Cart rather than user+restaurant+items); return the most specific type, accept the most general; return futures for IO so the signature communicates "remote call".
- Collapse duplicate methods by abstracting the parameter type (commentOnTweet + commentOnComment -> comment(Commentable)).
- Request/response DTOs instead of long positional parameter lists (mention for brownie points).
- Don't change a good public API because an internal step needs something; add internal primitives instead.
- Layering for server code: gateway (threads, JSON->object) -> controller (public API) -> service/logic -> DAO (one per table/access pattern) -> DB connector. Requests/responses/models in their own packages.

## 6. Algorithm and data structures
- Write per-operation complexity targets, then test candidate structures against each operation (logger: list/hashmap/heap/treemap each fail one op -> composite map + ordered queue).
- Use composite data structures and multiple indexes when one ordering can't serve all queries (cache: expiry index + LRU/LFU index).
- Prefer simple, explainable algorithms; mention the optimal one if it's NP-hard (Splitwise greedy vs subset-sum).
- Look for search speedups: binary search on sorted timelines; exponential jump + binary search for recurring events; hash to thread.

## 7. Flow / sequence
- Walk through the main use case call by call (placeOrder: create -> validate -> if invalid notify -> execute (deduct funds, exchange, update portfolio) -> notify success). Interviewers often ask for exactly this instead of full code.

## 8. Concurrency and consistency
- Find shared mutable state (read+write or write+write). Decide: lock (exclusivity), per-key single-thread executor (ordering), immutability + reference swap (consistent reads), concurrent collections, or a stated client-side guarantee. See `concurrency-and-async.md`.

## 9. Code
- Critical path first; stub IO (data sources, HTTP) - interviewers don't care about wiring.
- Use the IDE: generate constructors/getters, format; clean formatting impresses humans. AI assistants may or may not be allowed - ask.
- Use your language's strengths (Java types/exceptions/CompletableFuture, Go channels, C++ type safety).

## 10. Test
- Happy path from your whiteboard example, then edge cases (empty, ties, limits, 1 ms left, duplicates).
- Deterministic: inject timers/time, never rely on the system clock; remove unrelated components (AI) from the unit under test; test one unit at a time.
- Debug order: nulls/initialisation -> interaction (every structure updated everywhere it must be) -> concurrency.
- Concurrency tests need deliberate scheduling and a harness that respects client guarantees.

## 11. Extensions
- Show how new requirements slot in with minimal modification: new rule object, new strategy, new handler in the chain, new observer, new config field via builder.

## Timing for a 60-min round
- ~10 min clarify + requirements, ~15-20 min objects/class diagram/APIs, ~20-25 min code the core, remaining on tests/concurrency/extensions. In the Splitwise walkthrough: ~35 min to reach code, ~25 min coding.

## Tips repeated by the instructor
- Don't jump into code; don't jump into a requirements dump either - think and draw.
- Keep the whiteboard/notes visible while coding.
- Don't assume; ask (HLD vs LLD, scope, guarantees).
- Product thinking scores: e.g. Zomato - don't broadcast to employees, assign sequentially; assignment isn't real-time critical (food cooks), payment is.
- It's fine to not code everything; it's not fine to not *mention* concurrency, testing and trade-offs at senior levels.
