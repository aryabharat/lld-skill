# Concurrency and async in a component

Use this when a class or module is touched by more than one thread, does I/O on a request path, must keep per-key ordering, retries or delivers messages, or keeps several in-memory structures that must agree. It covers in-process LLD only. Service topology and sharding are out of scope.

**Contents:** Decision table. 1 Shared-state hazards. 2 Choosing a mechanism. 3 Ordering vs exclusivity. 4 Read-your-writes. 5 Never block request threads. 6 Request collapsing. 7 Write-through vs write-back. 8 Retries, DLQ, idempotency. 9 Push vs pull, back pressure, offsets. 10 Time. 11 Fail-open vs fail-closed. 12 Deadlock and stall pitfalls. 13 Multi-index consistency. 14 Testing. Interview-only notes.

## Decision table

| Signal in code or requirements | Mechanism | Rejected alternative and why | Refs |
|---|---|---|---|
| Several structures (map + sorted index) change together in one operation | One lock over the whole composite object, or a single writer thread | One concurrent collection per part: each part is safe but the pair can still be torn | [L84, L58] |
| Same-entity operations must apply in order, different entities can run in parallel | Keyed executor: N single-thread executors, `floorMod(hash(key), N)` | Shared pool: reorders across cores. One global thread: ordered but slow. Thread per key: too many threads | [L55, L62, L63, L65] |
| Read-mostly aggregate with an invariant (balances sum to zero, routing table, config) | Build a new immutable snapshot and swap one reference | In-place field-by-field updates: readers see impossible states | [L45, L85] |
| Read-mostly table and readers must never see stale data | Read-write lock | Snapshot swap: readers may see the previous version | [L45, L85] |
| One shared map, independent single-key operations | `ConcurrentHashMap` / `ConcurrentSkipListMap` | Hand-written locks: more code for the same result | [L65, L67, L85] |
| Handler would wait on a DB or remote call | Return a future, do the I/O on a separate bounded executor | Blocking the reader thread, or adding thousands of threads | [L54, L75, L76] |
| Many concurrent misses on one key | Put an in-flight future in the map and share it with every caller | One DB call per caller | [L53, L59] |
| Push delivery can fail | Capped retries on retryable errors only, then a DLQ, with idempotent consumers | Infinite retry, retrying every error, `printStackTrace` | [L61, L64, L68, L90] |
| Consumer falls behind under push | Back pressure per subscriber, or let it pull | Pushing at full rate until it collapses | [L71, L80, L90] |
| Order across producers | Sequence at a single point (keyed lane, append index) | Producer wall-clock timestamps: clock skew | [L61, L62] |
| Shared limiter or coordinator is unreachable | Fail open by default. Fail closed only when overrun is worse than downtime | Hard dependency: becomes a single point of failure | [L72, L74] |

## 1. Shared mutable state hazards

- **Torn reads.** One logical update writes two fields (A's and B's balance). A reader that arrives between the writes sees a state that never existed and is meaningless in the domain, not just old. Stale is acceptable. Inconsistent never is. [L45]
- **Check-then-act.** `containsKey` then `size() >= threshold` then `put` races even on a `ConcurrentHashMap`. Make the whole sequence atomic: one thread per partition, or a lock. [L56]
- **Read-increment-write.** `getNext(sub)` reading an offset and then bumping it, `threshold--`, and "index = size, then add" all lose updates under concurrency unless confined to one thread or made atomic. [L70, L80, L90]
- **Arrival order is not execution order.** On a multi-thread pool, a client's `set(A)` then `get(A)` can run on two cores, and the read can finish first. [L55]
- **Mutable objects behind caches or as sorted-map keys.** A cached mutable value can be handed out half-updated. A comparator key mutated in place corrupts tree or skip-list ordering. Cache immutable values. Remove, update, and re-insert keys. [L45, L57, L58]

## 2. Choosing a mechanism

The course reduces concurrency to two needs: **exclusivity** (locks) and **ordering** (ordered structures, or same key to same thread). Name which one you need before picking a tool. [L84]

### 2.1 One lock over the whole composite object

- **When** state is split across structures that must agree (pid map + start-time skip list, LRU map + list), **do** guard every update, delete and read-then-delete with one lock owned by the object. **Because** each concurrent part is safe on its own but the combination is not. **Flips when** an operation only creates entries independently in each structure (logger `start`). That can run without the lock if each part is a concurrent collection. [L84]
- Classify by CRUD. Create and plain reads can run concurrently. Update and delete (`poll` reads and deletes) take the exclusive lock. [L84]
- If almost every method takes the lock, the structure is effectively single-threaded. Say so, and say which operations still run in parallel. A class-wide lock is the simple "all guarantees" baseline, not a scalable answer. [L83, L84]
- Every lock needs guaranteed release (`finally`) and, for leases or distributed locks, an expiry so a dead holder cannot block everyone. [L55]

```java
void end(String pid) { lock.lock();
  try { Process p = byId.get(pid); p.end = clock.now();
        if (queue.firstEntry().getValue() == p) completeHeadWaiter(); }
  finally { lock.unlock(); } }
```

### 2.2 Keyed single-thread executor

- **When** operations on one entity must stay ordered but different entities can run in parallel, **do** route each task to `lanes[floorMod(hash(key), N)]`, where each lane is a single-thread executor. **Because** one thread runs its queue FIFO, so submission order becomes execution order with no per-key locks. **Unless** ordering is not needed (use a shared pool), state is also touched from outside the executor, or one key is hot enough to saturate a lane. [L55, L58, L62, L63, L65]
- Put it in its own `KeyedExecutor` class with a thread count taken from config. Domain classes should not manage threads. Offer `submit(key, Runnable) -> CompletionStage<Void>` and `get(key, Supplier<T>) -> CompletionStage<T>`. [L65]

```java
final class KeyedExecutor {
  private final ExecutorService[] lanes;            // each newSingleThreadExecutor()
  <T> CompletableFuture<T> get(Object key, Supplier<T> task) {
    return CompletableFuture.supplyAsync(task, lanes[Math.floorMod(key.hashCode(), lanes.length)]);
  }
}
```

**Choosing the narrowest key.** Use the smallest tuple whose ordering the requirement relies on. Start correct and coarse, then make it finer while the guarantee still holds. [L62, L68]

| Path | Key | Guarantee | Too coarse / too fine |
|---|---|---|---|
| Publish to topic | `hash(topic)` | Total order per topic across publishers | `(publisher, topic)` only orders one publisher's events. Valid only if that is the product's need |
| Subscriber pull | `hash(topic, subscriber)` | Per-subscriber order within a topic | `hash(subscriber)` serialises unrelated topics. `hash(topic)` orders all subscribers together for no reason |
| Logger start/end | `hash(processId)` | start before end per process | — |

- Keep separate reader and writer lane arrays when keys and guarantees differ. [L62]
- **Pitfalls (inferred):** colliding keys are serialised (correct, slower). A slow task blocks its lane. Raw `hashCode() % N` can be negative. Changing N breaks in-flight ordering. A `thenApply` running on the DB's completion thread leaves the lane, so re-enter with `thenApplyAsync(fn, laneFor(key))`. [L55, L59, L62, L63]
- **Production:** per-account ledger, per-orderId state machine, per-userId cache or session, webhook delivery per (customer, endpoint). This is the in-process form of Kafka partition-by-key. **Reviewer:** does every path that touches the entity go through the same router? A single direct call breaks the guarantee. [L58, L62, L65, L84]

### 2.3 Immutable snapshot and reference swap

- **When** a multi-field invariant must hold for concurrent readers and readers may see the previous version, **do** build a new immutable object and repoint an `AtomicReference`/volatile field in one step. **Because** a reader gets the whole old snapshot or the whole new one, never a mix, and reads never lock. **Flips when** readers must see the latest write. Then use a read-write lock. The instructor calls the snapshot "slightly easier" and picks it. [L45]
- The cost is one copy per write. `updateAndGet` retries on contention, so the rebuild function must be pure and cheap. For heavy rebuilds, serialise writers per key on a keyed executor and keep reads lock-free (inferred). [L45]
- Also fits a limiter client's config snapshot and an orchestrator's dependency graph (inferred). [L72, L85]
- A swap only protects memory. Persisting two balance changes still needs one DB transaction. [L45 (inferred)]

### 2.4 Concurrent collections and their limits

- `ConcurrentHashMap` for exact-key lookup. `ConcurrentSkipListMap` when you need ordering or a nearest/range query (`higherEntry`, `ceilingEntry`), because the JDK has no concurrent `TreeMap`. `CopyOnWriteArrayList` for small, iteration-heavy buckets. In real code, prefer them over hand-written locks. [L57, L67, L70, L85]
- **Limits:**
  - They make single calls atomic, not sequences. A composite still needs 2.1 or 2.2. [L84]
  - Lazily created inner maps must use `computeIfAbsent`. `getOrDefault(k, new Map())` followed by a write into the result silently loses the write. [L67, L69]
  - Skip-list maps reject null values. Use a sentinel. [L69]
  - Timestamp-keyed maps overwrite on ties. Use `(ts, seq)` keys or list buckets. [L57, L67 (inferred), L83 (inferred)]

### 2.5 Read-write lock

- **When** a table is read on every request and updated occasionally (orchestrator service table) and readers must not see a half-written entry or stale data, **do** take the write lock for updates and the read lock for lookups. **Because** reading during a write is the race to prevent. **Unless** stale-but-whole reads are fine, in which case a snapshot swap avoids reader locks entirely. [L45, L85]
- Make sure one request reads one version across lookup and the work that follows (topological sort). A snapshot gives you this for free (inferred). [L85]

## 3. Ordering vs exclusivity

- A lock gives exclusivity, not order. Two calls for one id that both take the lock can still run in either order. For "start before end" you need routing to one lane. [L84]
- Order only what is causally related (credit before debit for one account). Total order across unrelated keys gives up concurrency and gains no correctness. [L61, L63]
- A lane orders task submission, not completion of nested async work started inside a task. [L62 (inferred)]
- Out-of-order arrival over a network (end before start) has two answers: buffer the early event and reconcile, or state a client contract that start arrives first. The contract is an interview simplification. Real systems buffer and expire orphans. [L84]
- Do not add concurrency the business does not need. Sequential job offers to delivery partners avoid accept races. [L94]

## 4. Read-your-writes and consistency guarantees

- **Do** state the guarantee and what it does not cover before coding ("read-your-writes, nothing more"). The guarantee decides what blocks and on what. [L51, L52]
- **Read-your-writes:** after a client writes K, its later operations on K see the write, even if the DB write is still in flight. Two ways to get it: a per-key pending-write gate (hold later ops on K until the ack, release FIFO), or route all ops on K to one lane. The course builds the lane. [L52, L55]
- Block per key, never globally. Keys with no pending write are served at cache speed. [L52]
- Known gap the instructor accepts: an earlier-issued read can still see a later write. [L52]
- Stronger cross-node freshness needs every write to reach the DB, plus invalidation pushed to every cache holding the key. It costs more and the course does not build it. [L51]
- **Production:** settings caches where the next page load must show the save. A lost ack blocks the key forever, so add timeouts. Invalidate the entry when the DB rejects the write. [L52]

## 5. Never block request threads

- **When** a socket-reader or request thread would wait on a DB or remote call, **do** return a future at once and finish the work on another executor. **Because** reader pools are small (tens of threads). A few slow calls drain them, and fast requests queue behind slow ones: head-of-line blocking, with a fast backend sitting idle. **Unless** the dependency is in-process and reliably fast (inferred). [L54]
- Use the language's future/promise. Do not hand-roll fill-and-notify or polling slots. Every future must complete on success, on exception and on timeout. [L54]
- Use composable futures (`thenApply/thenCompose/whenComplete`), not `isDone()` loops or `get()`. A `join()` on a future you "know" is complete means the method takes the wrong type, so move the future boundary. [L56, L59, L79]
- **Which thread runs the continuation:** non-async `thenAccept/thenApply` runs on whichever thread completed the future, or on the caller's thread. For stages that may block, use `...Async(fn, executor)` with an explicit executor. [L75]
- **Where pools live:** a gateway/dispatch layer deserialises the request and hands it to its own executor before any controller runs. The DB-access class owns its own pool. Controllers hold no thread code. [L75, L76]
- **Embedded clients/SDKs:** run your own server I/O on a small private pool (1-2 threads, not 10). Run caller-supplied callbacks in the caller's context, because the caller knows their cost. Document which thread runs what. [L77, L79, L80]
- **Signatures as documentation:** a method backed by I/O returns `CompletableFuture<T>` (`<Void>` for writes), even with one caller today. A purely local decision (`shouldAccept`) returns a plain `boolean`. [L73, L79, L80]
- **Constructors must not block on remote data.** Fetch at the composition root or in an async factory, then inject the resolved object. [L78, L79]

```java
server.getServiceConfig("profile")
      .thenApply(cfg -> new RateLimiterClient(new SlidingWindow(cfg)));   // no I/O in constructors
```

- **Reviewer checks:** no `.get()`/`.join()` on request threads. Every `get` has a timeout. Executors are bounded and named. Failures are handled (`exceptionally`), not dropped. No `throws Exception`. [L54, L75, L76, L79]

## 6. Request collapsing

- **When** concurrent callers can miss on the same key and the load is I/O, **do** put the future placeholder in the map on the first miss and return that same future to later callers. **Because** you make one I/O call for N callers, and they all see the same value. **Unless** callers need independent results or the value changes during the load. [L53, L59]
- This forces the map to hold `CompletableFuture<Record<V>>` and `addToCache` to accept a value future. Shorter call sites confirm the refactor. [L59]

```java
CompletableFuture<Record<V>> addToCache(K k, CompletableFuture<V> valueF) {
  evictIfNeeded();
  CompletableFuture<Record<V>> rf = valueF.thenApply(v -> index(k, new Record<>(v, clock.now())));
  map.put(k, rf);                       // placeholder visible at once
  return rf;
}
```

- **Production:** single-flight loading (Caffeine `AsyncLoadingCache`, Go `singleflight`). **Reviewer (inferred):** remove a failed future from the map, or later readers get the cached error. Decide whether placeholders count toward capacity and when TTL starts. [L59]

## 7. Write-through vs write-back

| | Write-through | Write-back |
|---|---|---|
| Shape | Persist first, update memory only on success: `persist(k,v).thenApply(x -> v)` | Update memory now, persist asynchronously or in batches |
| Gains | DB always current, nothing lives only in memory, simpler | Fewer, batched writes, protects the DB from hot keys |
| Costs | One synchronous DB write per update | Data lost on crash, peers stale, harder to debug |
| Use for | Money, balances, orders. The instructor's default | Counters, view stats, last-seen. Count in memory and flush periodically |
| Refs | [L51, L56, L59] | [L51, L56, L88] |

- The cache must never show a value the store rejected. [L56]
- The course's write-back is fire-and-forget. The batched dirty-flush variant was judged too much bookkeeping for the exercise. Either way, log or meter persist failures and flush on shutdown. [L51, L56]

## 8. Retries, DLQ, idempotency

- **Retry only retryable errors.** The caller defines a `RetryableException`. Anything else is rethrown on the first attempt, because bad input fails the same way every time. When attempts run out, throw a distinct `RetryLimitExceededException`. [L64]
- **Strategy:** `RetryAlgorithm` holds the shared loop and subclasses provide only the wait (exponential `base * 2^(attempt-1)`, or fixed). Max attempts and base wait come from the constructor or config. Wait through an injected timer. [L64]
- Production additions (inferred): cap the backoff, add jitter, use idempotent operations. [L64, L71]
- **DLQ:** after the last attempt, publish `FailureEvent(event, failedAt, exception)` to a dead-letter queue. The DLQ can be another bus instance. Never just log and drop. A DLQ nobody drains is slower data loss, and a DLQ publish failure must not recurse (inferred). [L61, L68, L90]
- **Idempotency:** publish is idempotent on a producer-assigned event id that stays stable across retries. A duplicate is acknowledged, not reprocessed. The dedup set needs a TTL or window. Client-generated ids give idempotent creates. Consumers must still be idempotent, because the bus can deliver duplicates. [L60, L61, L86]
- **Events are immutable.** Corrections are new compensating events. Prefer soft deletes or no delete API. [L61, L90]
- **Pitfall:** `Thread.sleep` inside a retry on a keyed lane stalls every later event for that key. Use a scheduled executor, or accept the stall on purpose because it preserves order. [L64 (inferred)]

## 9. Delivery: push vs pull, back pressure, offsets

- **Push** is an internal effect of `add`, not a public API. Only push consumers register. **Pull** consumers ask for "next after my position". [L66, L90]
- Model the relationship as a `Subscription{id, subscriberId, topic, type, filter}`, so one subscriber can hold several subscriptions. Evaluate filters on the bus before any I/O. [L66]
- **Offsets are kept by the broker** per (topic, subscriber), and messages are not deleted on read. Otherwise every consumer must persist and recover its own cursor. Replay goes through an admin "reset offset". [L67, L90]
- Store cursors as positional indexes into an append-only per-topic log, initialised at subscribe time. The instructor's first timestamp/event-id cursor put every subscriber at the tail. He abandoned it in L69 and settled on a positional index in L70. A time index (`ConcurrentSkipListMap<ts, index>`) serves "replay from T". [L67, L69, L70]
- **Back pressure:** per push subscriber, lower the send rate on failures and keep the rest buffered for retry. Pull is self-paced and needs none. In a limiter, shrink the threshold on rejection, grow it by a fraction or not at all (+1 per accept means it never rejects), and clamp between min and max (inferred). [L71, L80, L90]
- One slow subscriber must not block the fan-out loop. Give each subscriber its own queue or executor (inferred). [L90]
- At a connection cap, evict the least recently used connection. If eviction thrashes, scale out. [L88]

## 10. Time handling

- Inject a clock or timer into anything that reads time or sleeps. Production uses a singleton, tests use a fake. [L57, L64, L69, L83]
- Read the clock once per logical operation and reuse the value for every structure it stamps. [L57, L83]
- Normalise units once (TTL in seconds vs clock in millis was a live bug). [L57, L81]
- TTL counts from load time, not last access. Idle timeout is a different feature. [L57]
- Do not order events by producer wall-clock timestamps. Skew lets a later event carry an earlier stamp. Vector clocks and clock sync work but are heavier than this needs. Sequence at a single point, and assign append timestamps inside the bus under the topic's lane (inferred). [L61, L70]
- Use a monotonic clock (`nanoTime`) for intervals and windows. [L64, L81 (inferred)]

## 11. Fail-open vs fail-closed

- **When** a shared guard (rate-limiter server, heartbeat) times out, **do** fail open: keep the last known state and admit requests. **Because** failing closed makes the guard a single point of failure for every caller. **Unless** overrun is worse than downtime (paid quotas, a fragile downstream). Then reject, and accept the SPOF. [L72, L74]
- Keep the decision on the hot path local and cheap (an in-process client with cached config), and sync aggregates on a fixed interval set independently of the limit window. The global limit is then approximate. Overshoot is bounded by instances x rate x interval (inferred). [L72, L74]
- Durable queues fail the other way: acknowledge publish only after the DB write. On repeated failure, return a retryable "unavailable" error. [L90]
- Limiter rejections are soft, retryable failures (429/503, inferred). [L71]

## 12. Deadlock and stall pitfalls

- **Lock held while waiting (the logger flaw).** In L84, `poll` takes the lock, registers a waiter future, then calls `f.get(3s)` while still holding it. `end`, which completes that future, needs the same lock, so it stalls until `poll` times out. The instructor also says several polls can block at once, which the exclusive lock makes impossible. **Final position (inferred):** never wait while holding the lock. Use `Condition.await` on the same lock, which releases it, or register the waiter, unlock, then wait. Remove waiters that time out. [L84]
- **Wait with a deadline.** Every blocking get has a timeout, and a timeout counts as a failed request. Prefer returning the future in-process. Block only when the result must cross an API boundary that cannot carry a future. [L84]
- **Head of line in a lane or ordered buffer.** One stuck process at the head holds every later completion. Add expiry, a maximum buffer size, and metrics on head age. [L83, L84 (inferred)]
- **Blocking inside a lane** (DB call, retry sleep) stalls every key that shares the lane. [L58, L64]
- **Busy-wait or `Thread.yield`** only hints the scheduler. Have the producer complete a future. [L84]
- **Mass reconnect** after dropping all connections or a gateway redeploy is a thundering herd. Keep socket holders separate from business code. [L88]

## 13. Multi-index consistency

The cache keeps a map, an expiry index (load time to keys) and a priority index (AccessDetails to keys, LRU or LFU comparator). The bus keeps a log, an id index and a timestamp index. The logger keeps a map and a start-time queue. [L57, L58, L68, L70, L83]

- **One add and one remove routine** touch every structure. Get-miss, set and hot load all go through `addToCache`. Publish goes through `addEventToBus`. Side doors leave structures out of sync. [L58, L59, L68]
- Overwriting or expiring a key removes its old entries from every index. Otherwise index pollution leaks memory and picks wrong victims. [L58]
- Run the capacity check before every insert, including a get-miss. [L58]
- Evict exactly one key from a shared bucket (`firstEntry`, not `pollFirstEntry`). Drain only entries that are really expired before evicting a live one. [L58]
- Indexes store keys, not records. Encode the policy only in the comparator. [L58]
- A shared mutable object referenced from two indexes can be changed once, provided the changed field is not a sort key. If it is, remove and re-insert. [L83]
- Collapse parallel maps keyed by the same id into one aggregate (`Topic`) with methods like `getNext(sub)`, so that read-then-act stays inside the owner. [L68, L90]
- Guard the whole set with 2.1, or confine it to 2.2. [L84]

## 14. Concurrency testing

- Fix bugs in phases: nulls, then interactions between structures, then concurrency. Each class of bug hides the next. For the null pass, list every field and its write sites. [L69]
- **Ordering:** a harness that follows the real client contract fires thousands of randomly interleaved commands through a large pool and asserts output order. Also run it with order inverted. Without lock plus striping, the test should fail. [L84]
- **Keyed lanes:** interleave many `set(k,v_i)/get(k)` calls with random delays and assert read-your-writes. A slow task on key A must not delay key B on another lane. N=1 forces full serialisation. Include a negative hashCode. [L55, L62, L63, L65]
- **Invariants:** hammer edits while reading and assert every read sums to zero. After random operations, assert the map's key set equals each index's key set. [L45, L58, L68]
- **Collapsing:** N concurrent gets on a counting fake source make exactly one load. A failed load is not served forever. [L59]
- **Async:** with a slow fake DB, the reader thread still accepts requests. A slow write then a read on the same key returns the new value. [L52, L54, L75]
- **Retry:** with a fake timer, assert waits of 1000, 2000, 4000, then `RetryLimitExceeded`, then the DLQ. Non-retryable errors fail at once. [L61, L64]
- **Time and fail-open:** a fake clock for TTL and window boundaries. Kill the coordinator and assert requests still pass. [L57, L72, L81]
- Assert on returned values, not printed output. [L83, L84]

## Interview-only notes

- One-hour LLD round: name the concurrency risks and the fix. Machine-coding or long rounds: implement them with tests. [L53, L85]
- Strong signals: name the anomaly (torn read, stale read after own write), offer two mechanisms and justify the pick, explain why one thread gives order and why affinity matters on multi-core. [L45, L52, L55]
- Logger: the algorithm is about 60%. Expect follow-ups on blocking poll, concurrency and tests. [L83]
- Many requests sharing an expensive resource: the expected answer is an object or connection pool. [L94]
- Common misses: a thread pool with no key routing, a lock with no release policy, `synchronized` everywhere, blocking on a returned future. [L54, L55, L84]
