# Concurrency, async and consistency (course techniques)

## Core statement
Concurrency needs two things: **exclusivity** (locks) and **ordering** (ordered data structures, or sequential execution by assigning the same key to the same thread). Plus a third tool used throughout: **immutability**.

## Find the hazards (CRUD lens)
- Creates (append-only to concurrent structures) usually can run concurrently.
- Reads concurrent with writes, and write-write on shared data, need care. Poll = read + delete.
- Composite structures (map + ordered queue) are not atomic even if each part is a concurrent collection.
- Look for: read-modify-write sequences, two-step updates (both balances of an expense), check-then-act (key absent -> load), event ordering (end before start), shared config updated while read.

## Techniques
### Locks
- `ReentrantLock` with `lock(); try { ... } finally { unlock(); }` around operations that mutate shared composite state (logger poll and end). Locking everything = single-threaded; keep creates outside the lock when safe.
- Read/write locks for read-mostly shared tables (orchestrator dependency table).
- Lock holder dying: use lock expiry or always release in finally.

### Per-key thread assignment (ordering without global locks)
- `executors[hash(key) % n]` where each executor is single-threaded. Same key -> same thread -> sequential; different keys run concurrently. Needs **data locality and sequential execution**.
- Choose the key by the ordering guarantee wanted:
  - Cache: key -> read-your-writes per key.
  - Logger: processId -> start always processed before end.
  - Event bus reads: hash(subscriber, topic) -> per-subscriber-per-topic order, concurrency across topics/subscribers.
  - Event bus writes: hash(topic) -> total order per topic across publishers (stronger). hash(publisher, topic) only orders per publisher.
- Causal ordering: order only dependent tasks; one thread per user is impossible at scale, so many keys share a thread - accepted cost.
- Encapsulate in a `KeyedExecutor { submit(key, Runnable); get(key, Supplier<T>) }`.
- Assumes upstream partitioning sends all requests for a key to the same node.

### Immutability + reference swap
- Build a new immutable object (balance map, Amount.add returns new) and swap the reference. Readers see all-old or all-new: stale but never inconsistent (eventual consistency). Prefer over locks for cached read-heavy data (Splitwise group balances).
- Events are immutable (no update/delete; corrections are new events) - simplifies event buses and financial systems.

### Concurrent collections
- `ConcurrentHashMap`, `ConcurrentSkipListMap` (sorted, log n - Java has no concurrent TreeMap), `CopyOnWriteArrayList`, blocking queues. Use `putIfAbsent`/`computeIfAbsent`/`getOrDefault` to avoid null-key races and NPEs.

### Client guarantees
- Legitimately push some ordering to the client ("start reaches us before end") and state it; the server then guarantees execution order. Alternative: buffer out-of-order events until the predecessor arrives.

## Async with futures
- Never block request-reading threads on IO: a small fixed pool blocked on slow calls stops the server reading sockets; **head-of-line blocking** - slow requests (remote DB) starve fast ones.
- Return `CompletableFuture` (container for result or exception); compose with `thenApply/thenCompose/thenAccept/whenComplete/exceptionally`; `*Async(fn, executor)` to run on a chosen pool (callbacks otherwise run on the completing thread).
- Thread ownership: gateway owns request-dispatch pool; DB layer owns its pool; a client library owns a small pool only for *its* IO; caller-supplied callbacks run where the caller decides.
- Blocking APIs (logger poll) use `future.get(timeout)`; every API should have a timeout. Prefer returning the future when the API allows.
- Don't call `.get()` in constructors - inject already-fetched dependencies.
- Don't throw generic `Exception`; throw specific ones the caller can handle.

## Request collapsing
- Store the in-flight future in the map on first miss; concurrent requests for the same key get the same future; one IO call serves all.

## Retries, DLQ, back pressure
- Retry only `RetryableException`s (DB down), not validation errors. Exponential backoff (1, 2, 4 s...) or periodic; max attempts; then dead letter queue (itself just another bus) for diagnosis.
- Don't auto-retry money operations (orders) - fail and notify; user re-places.
- Back pressure: lower the send/accept rate when the downstream fails (push only; pull consumers self-regulate). Forward pressure must be tiny (+0.1 per success), never +1 per success.
- Idempotency: client-generated ids (or event ids) let servers ignore duplicates from retries. Make ids collision-proof (userId + timestamp + machine/sequence, Snowflake).

## Consistency guarantees for caches
- Read-your-own-writes via per-key thread ordering. Write-through (consistent, slower) vs write-back (fast, risk of loss, others read stale). Strongest: DB notifies all caches.

## Delivery mechanisms (client <-> server)
- Short polling (simple, wasteful), long polling (server holds until event), SSE (server push over one HTTP connection - best for one-way live updates), WebSockets (full duplex - needed only when either side sends anytime, e.g. chat).
- Connection limits: evict LRU connections, not all (thundering herd on reconnect); thrashing means scale out; decouple connection gateways from business deploys.

## Testing concurrency
- Deterministic time (inject Timer), large randomised interleavings with a harness that respects client guarantees, assert ordering of outputs; verify by inverting inputs.
