# Case studies index

Use this to pick the worked design closest to the problem in front of you. Find your problem in the first table, or in the nearest-neighbour table if the course did not cover it, then open the named file and reuse its techniques.

Each case study has the same sections: problem and scope; requirements (full -> shortlisted); entities and APIs; core algorithm and data structures; concurrency; patterns used and rejected; tests; extensions and trade-offs; pitfalls the course hit; what transfers to production.

## Course case studies

| Problem | Type | Key techniques | File |
|---|---|---|---|
| Turn-based game engine (refactor story) | Refactoring series, SOLID | One change request -> one principle; rule engine for win checks; Prototype for AI trials; chain of responsibility for AI placements; Factory for game creation; Memento undo; Flyweight; Observer for notifications [L0-L41] | `game-engine.md` |
| Tic-tac-toe (interview) | Small LLD | Only the last move can win; check lines through that cell; O(1) running row/col/diagonal sums; validate input before updating aggregates [L93] | `tic-tac-toe.md` |
| Chess | Machine coding (live) | Abstract piece + template-method `move` with a per-piece rule; copy board, apply, check for check; derive state rather than store flags; aggregate owns cells [L82] | `chess.md` |
| Splitwise | Machine coding | Net balances, greedy over two max-heaps (O(n log n), at most n-1 edges, not optimal); value objects for money; algorithm before models in timed rounds [L42-L50] | `splitwise.md` |
| In-process cache | Machine coding, concurrency | Map of futures (request collapsing); separate expiry and eviction indexes; LRU/LFU via injected comparator; per-key thread assignment for read-your-writes; hot loading [L51-L59] | `cache.md` |
| Event bus | Machine coding, concurrency | Event objects carry all inputs; retry as Strategy with injectable timer; `KeyedExecutor` for per-key ordering; `Subscription` as first-class entity (push/pull, filter); wrapper classes; tests [L60-L70] | `event-bus.md` |
| Rate limiter | Machine coding, distributed client | Embedded client decides locally, central server owns config; pluggable algorithm with sliding-window default; adaptive threshold (backpressure); evict stale timestamps from the sorted head; caller owns callback threads [L71-L81] | `rate-limiter.md` |
| Logger (start/end/poll in start order) | Algorithmic LLD, concurrency | Composite structure: hash map by id + ordered map by start time on shared objects; blocking poll; one lock around the composite, not per-part concurrent collections; exclusivity vs ordering [L83-L84] | `logger.md` |
| Orchestration service | LLD (live) | Validate -> decode -> topo sort -> call pipeline; interface per stage; routing as data; read-mostly table guarded or swapped as immutable snapshot [L85] | `orchestration-service.md` |
| Calendar (recurring events) | LLD + schema (live) | Store a rule, generate occurrences on read; split blueprints on edit (Prototype, Builder); jump to window in O(log n); join table for M:N; client IDs for idempotency [L86] | `calendar.md` |
| Stock trading (broker) | LLD (live) | Scope to 3-4 features; Strategy for buy/sell; Observer only when subscribers vary; enum vs boolean; map for O(1) holdings; server-side price [L87] | `stock-trading.md` |
| Live scores | Component design (live) | Pick SSE / long poll / WebSocket by communication direction; LRU-evicted connection pool; avoid mass drops and reconnect storms; split gateway from logic; scale out on thrash [L88] | `live-scores.md` |
| Twitter with trending | LLD mock interview (live) | Extract capability bases (`Reactable`, `Commentable`); one service method per operation; hybrid push/pull timeline; binary search on `lastSeen`; threshold event at the point of mutation [L89] | `twitter.md` |
| Pub/sub message queue | Engineering-product LLD (live) | APIs first; push internal to publish; retain messages, broker-held pull offsets; collapse parallel maps into a `Topic` aggregate; retry + DLQ; back pressure for push only [L90] | `message-queue.md` |
| Coupon rule engine | LLD (live) | Rules as serializable predicates over one context; generic AND engine; discovery via indexed metadata, not rule search; per-user usage ledger; clubbing policy [L91] | `coupon-engine.md` |
| DB schema for GitHub / Git storage | Schema design (live) | Features -> APIs -> tables; access patterns pick layout; junction tables; ACL tuples (Zanzibar-style); content-addressed immutable trees; refs as root pointers [L92] | `git-schema.md` |
| Food delivery assignment (Zomato) | LLD mock interview | Find-select-persist assignment; sequential offer with timeout vs broadcast; assign late and async; status enum + append-only log; Observer fan-out; resource pool [L94] | `food-delivery-assignment.md` |

## Nearest neighbour for problems not in the course

All mappings below are (inferred): the course did not design these systems, but the listed techniques come from the cited case studies.

| Problem | Closest case studies | What transfers |
|---|---|---|
| Parking lot | `food-delivery-assignment.md`, `stock-trading.md`, `game-engine.md` | Spot allocation as find-select-persist with a conditional write; enums for spot type and ticket state; Strategy for allocation and pricing; resource-pool thinking for a capped set of slots |
| BookMyShow (seat booking) | `git-schema.md`, `calendar.md`, `cache.md` | Schema from features then access patterns (no double booking was a reported schema question); join tables for show-seat-booking; client IDs for idempotent booking; per-key ordering or a lock per show for seat holds; hold expiry like TTL |
| Elevator | `logger.md`, `orchestration-service.md`, `game-engine.md` | Ordered structures for pending floors per direction; one thread or lock per elevator for ordering; pluggable scheduling Strategy; State only if transitions are real (the game engine rejected State where they were not) |
| Library management | `git-schema.md`, `coupon-engine.md`, `stock-trading.md` | Junction tables for member-loan-copy; per-user usage records for borrow limits; fine rules as predicates; enums for copy status |
| Ride matching (Uber) | `food-delivery-assignment.md`, `live-scores.md` | Broadcast, first accept wins, with a conditional assign to settle accept races; geo ranking helper; push location updates over a held connection; connection-cap and reconnect rules |
| Notification service | `message-queue.md`, `event-bus.md`, `stock-trading.md`, `live-scores.md` | Channel interface per medium; Observer only where subscribers vary; retry with backoff + DLQ; per-subscriber back pressure; SSE for in-app delivery; targeting rules as predicates (coupon engine) |
| URL shortener | `calendar.md`, `cache.md`, `git-schema.md` | ID generation (server vs client, Snowflake-style composition); read-through cache with request collapsing for hot links; content-addressed keys if dedup is wanted |
| Inventory management | `orchestration-service.md`, `splitwise.md`, `coupon-engine.md` | Validate before side effects; atomic check-and-decrement per SKU; ledger of movements rather than a bare counter; reservation rules as predicates |
| Snake and ladder | `tic-tac-toe.md`, `game-engine.md`, `chess.md` | Board and rule separation; jumps as data (map from cell to destination); dice as injectable Strategy for tests; turn loop from the game engine; derive state rather than store flags |
| Vending machine | `game-engine.md`, `stock-trading.md`, `food-delivery-assignment.md` | State pattern where transitions are real (idle, has money, dispensing); enums for product and coin; status enum plus event log; inventory map keyed by slot |
| Payment wallet | `splitwise.md`, `stock-trading.md`, `rate-limiter.md` | Money as long minor units; append-only ledger, balances derived; no auto-retry of business failures; idempotency keys; atomic debit with funds check; per-user rate limits |
| Job scheduler | `calendar.md`, `event-bus.md`, `orchestration-service.md`, `cache.md` | Recurring jobs stored as cron-like rules, next run computed by jumping; dependency DAG via topological sort; retry Strategy with injectable timer; `KeyedExecutor` for per-job ordering; expiry-ordered index for due jobs |

## How to use a case study in real work

- Match on the shape of the pain (shared mutable table, recurring data, skewed fan-out, open-ended rules), not on the product name.
- Read "Patterns used and rejected" first: the course's value is knowing when not to apply something.
- Lift the tests list into your PR: each case study's tests are the review checklist for that shape.
