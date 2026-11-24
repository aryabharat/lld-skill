# Design patterns as taught in the course (when to use, when not, origin example)

Patterns are "blueprints for thinking" - reuse others' conclusions. They compose (Chain of Responsibility needed Singleton). Use them where the code needs them; reject them when they don't fit.

## Creational

### Prototype
- **What**: object creates a fresh copy of itself with requested changes (`board.copy()`, `player.flip()`), clone logic lives in the object.
- **Use when**: exploring hypothetical states without mutating the real one (AI look-ahead), snapshots for history, cloning a recurring-event blueprint to split it, objects that spawn similar objects (threads, calendar recurrences).
- **Watch**: shallow vs deep copy - reference copy is only safe for immutable members or full reference replacement.
- **Trade-off vs undo**: copy = simple, thread-safe, generic, more memory; undo = cheap, gives history, unsafe concurrently, some undos cascade (chess).

### Builder
- **What**: fluent setters per field returning `this`, then `build()`.
- **Use when**: many optional parameters / telescoping constructors; adding a field must not break callers (GameInfo + numberOfMoves + forkCell: only builder changed); commands with many optional fields (email: link, template).
- **Don't**: when the builder takes one object and builds one way - use a constructor. Base builder returning base type breaks callers needing subtypes - compose builders instead.
- **Vs Factory**: Builder = many settable params, little init logic. Factory = complex init logic hidden behind few params.

### Factory
- **What**: a class whose job is creating complex objects from simple parameters (`GameFactory.createGame(maxTimePerMove, maxTimePerPlayer)` creates config, board, defaults).
- **Use when**: construction requires knowing many implicit defaults or sub-objects; creation varies by type (pizza bases/baking temps); business rules about creation (profile exists? no simultaneous games) shouldn't live in the object or be repeated.
- **Test** the factory separately from the objects it builds.

### Singleton
- **What**: one instance per class; private constructor + static getter (lazy).
- **Use when**: stateless strategy/handler objects (placements in the chain), shared timers, pools.
- **Watch**: thread-safe init (synchronized or let a DI container/annotation do it - Dagger/Guice/Spring); single state doesn't make concurrent *updates* safe. Interfaces can't force static methods, so boilerplate repeats - a generic `getIfNull(instance, supplier)` helps. In interviews say you'd use a library unless asked to hand-write it.

### Object pool / Flyweight
- **Object pool**: reuse expensive objects (DB connections, notification senders, threads) instead of creating/destroying - the answer the Zomato mock interviewer wanted for many workers contending for a resource.
- **Flyweight / shared immutables**: share intrinsic immutable values (Cell(row,col) cache, enum symbols; Google Monarch shares timestamps across series). Pre-populating removes null checks but hard-codes size - trade-off.

## Structural

### Proxy
- **What**: stand-in with the same interface that lazily creates the heavy object on real use (lazy loading). Uses: DB connections, heavy objects.
- **Trade-off**: transparent to callers but any call may materialise the full object and every method must delegate. When the goal is minimal memory (history snapshots), a compact representation + constructor-from-representation is simpler.

### Composite objects / wrapper types (not GoF, heavily used)
- Name and encapsulate nested/parallel structures (BalanceMap, PaymentGraph, RuleSet implements Iterable, Topic). Value-wrapper ids (Topic, EventId, EntityId).

## Behavioural

### Strategy
- **What**: interchangeable algorithms behind one interface, chosen at runtime/config.
- **Use when**: the input or configuration decides the algorithm and algorithms are independent: AI move strategies (basic/smart/optimal), buy vs sell order execution, rate-limiter algorithms (sliding window, token/leaky bucket) with a default, cache eviction comparator (LRU/LFU), retry (exponential/periodic), persistence (write-through/back), notification channels (email/SMS).
- **Vs State**: State needs a sparse, action-driven transition graph; if transitions depend on everything and form a full mesh, State won't help.

### State
- **Use when**: an object moves through a clear, sparse set of states via actions (order lifecycle, call states).
- **Rejected in course** for `suggestMove`: next state couldn't be derived from the current state (depends on whole board/time), transition logic would be duplicated in every state, 5x5 full-mesh transitions. "Evaluate against the old code before investing."

### Chain of Responsibility
- **What**: handlers in an explicit order, each tries and/or passes to `next()` (`Optional<Cell> place(board, player)`).
- **Use when**: ordered fallbacks: win -> block -> fork -> block fork -> centre -> corner; validation pipelines; request filters.
- **Pro**: new step = new class; order explicit in code (unlike a rule set). **Con**: can't see the whole flow at once; following the chain is a "rabbit hole".
- Often combined with Singleton handlers.

### Rule engine (rules as data)
- **What**: list of rule objects (`Function<T, Result>`); evaluator iterates; rules can come from config/DB/admin dashboards.
- **Use when**: many independent, order-independent conditions that change often (game-over conditions, coupon validity, fork detection, alerting).
- **Don't** when rules depend on each other/ordering (someone puts them in a Set and breaks everything) - make them mutually exclusive or use a chain/plain ordered code with extracted methods.
- Pull queryable metadata out of rule blobs into indexed columns (coupon userId/restaurantId/platform/validity).

### Iterator
- `hasNext()/next()` to hide traversal. Rejected for 2-D board traversal: a `BiFunction<i,j,cell>` addresses any cell directly; iterators only know "next". Pick the abstraction that fits the traversal shape.

### Memento
- **What**: history of snapshots for undo/redo/time-travel (`History {add, getBoardAtMove, undo}`), internal list/map swappable behind the API.
- **Watch**: memory (full snapshot per move) - pair with compact representations; truncate future snapshots when jumping back; list-remove-index-shift bug.

### Command
- **What**: wrap a request as an object (`SendEmailCommand`) executed by a service (`execute(command)`).
- **Use when**: the request has many evolving parameters, construction needs business logic (country-specific links) that belongs neither in the caller nor in the executor. Separates invoking, describing, doing. Modern form = message/event; CQRS derives from it.

### Observer / Publisher-Subscriber
- **What**: subject keeps a list of observers implementing a common interface; notifies on change. Pub-sub adds a bus/topic between publishers and subscribers.
- **Use when**: a variable, runtime-changing set of interested parties (order status -> SMS, invoice, analytics, payment; weather station displays; game events -> email/SMS/in-app).
- **Don't** when there's one fixed recipient (notifying the user who placed the order).
- Hard-coding `a.update(); b.update();` violates OCP, is hard to test, doesn't scale, tightly couples.
- Producer shouldn't know consumers; consumers shouldn't contain polling loops; dead letter queues for failed deliveries.

### Template method (implicit)
- Base class implements the common algorithm and calls abstract hooks: chess `Piece.move()` (own-piece check, simulate, own-king-in-check, capture, check enemy king) calling abstract `isValidMove`; `RetryAlgorithm.attempt` with backoff policy.

## Quick picker
| Problem shape | Pattern |
|---|---|
| Many optional fields | Builder |
| Complex creation / defaults / creation rules | Factory |
| Copy-and-modify, hypothetical states | Prototype |
| One shared stateless instance | Singleton |
| Expensive reusable resources | Object pool |
| Lazy heavy object | Proxy |
| Undo/history | Memento (or replay moves) |
| Swap algorithm by config/input | Strategy |
| Ordered fallbacks / pipeline | Chain of Responsibility |
| Many independent changing conditions | Rule engine |
| Sparse lifecycle transitions | State |
| Request with many params + build logic | Command (+ Builder) |
| Fan-out to changing listeners | Observer / pub-sub |
| Shared algorithm with per-type steps | Template method / abstract base |
