# Data modeling, schemas, APIs and data structures

Use this when: deciding the classes, tables, method signatures or in-memory structures of a component, or reviewing a PR that adds entities, columns, endpoints or indexes.

Contents: 1. Objects and entities - 2. Storage and schema - 3. API design - 4. Data structures from operations - Interview-only notes

---

## 1. Objects and entities

### Finding the objects
- **When** the requirement is fuzzy. **Do** write the caller's public signatures first; their nouns are your classes. Walk each API against the model ("enough data to persist or compute this?"); gaps become fields. **Because** behaviour-first models carry only state something reads. **Flips when** it is a consumer product: actors and flows drive it. [L3, L43, L47, L50, L90]
- **Reviewer check:** every field on a new entity is read by some behaviour in the PR. Fields "for later" and empty packages are smells. [L4, L50]

### What defines an object vs what is an association
- **When** a collection sits on an entity. **Do** ask "does this field define the object?" A group is its id, name, image and members; its expenses do not define it and grow without bound. Move them into an association (`GroupExpenses{groupId, expenses}`) or a child table keyed by parent id. **Because** embedding bloats the object, every cache entry and every row lock. [L43, L86]
- **When** an actor can relate to a resource more than once (one subscriber, two subscriptions to a topic with different filters). **Do** make the relationship a first-class entity with its own id (`Subscription{id, subscriberId, topicId, mode, filter}`). **Because** the actor id cannot tell them apart, and per-relationship attributes (mode, filter, RSVP) need a home. L90 later found a pull subscriber needs no registration at all, so register only push consumers. [L66, L86]
- **When** two maps have the same shape and differ only in how they are read (push, pull). **Do** merge into one whose elements carry a type enum. **Flips when** variants have truly different data or lifecycles; then they are separate types. [L66]
- **When** several maps share a key and are always used together (`topicId -> messages`, `topicId -> subscribers`, `topicId -> offsets`). **Do** replace them with one `id -> Aggregate` map; the aggregate owns the parts. [L68, L90]
- **When** a field is a mutated collection (holdings, watchlist, active orders). **Do** give it its own class. **Because** add/remove is behaviour that needs a named owner. [L87]
- **When** an object would need dozens of setters. **Do** split and compose (`Expense = BalanceMap + metadata`); keep editable metadata apart from the core state algorithms read. [L43, L46]

### Value objects
- **When** a number is money. **Do** wrap it in an immutable `Amount{currency, value}` with `add()` returning a new instance; use minor units or decimal, never double; reject mixed currencies. **Because** an amount without currency cannot be summed safely, and immutability lets you aggregate without shared state moving. [L43, L47, L87]
- **Pitfall:** an `add` that returns its argument makes every total equal the last input. Unit-test arithmetic primitives on their own. [L49]

### Result objects instead of booleans
- **When** an answer has more than two outcomes or carries data (over + winner, or draw). **Do** return a result type (`GameResult`, `ValidationResult{ok, reason}`). **Because** a boolean forces a second call or hidden state. Prefer an enum status over sentinels like `"-"`. [L3, L91]
- **When** a field has a closed set of values that may grow (order type, order state). **Do** use an enum. **Flips when** it is truly binary forever (buy/sell). The instructor's `isLimitOrder` became `OrderType`. [L87]
- Endpoints that return nothing today still get a response type (empty `UpdateResponse` with the request id), so fields can be added without changing the signature. [L75]

### Wrapper types for ids and nested collections
- **When** signatures or maps use raw `String`/`long` for identifiers. **Do** wrap each (`Topic`, `EventId`) as an immutable type with value equality (records, Kotlin value classes, TS branded types, Go named types). **Because** swapped arguments (`refund(orderId, userId)`) stop compiling. **Flips when** the code is a throwaway; the instructor calls it possibly overkill and picks clarity. [L68]
  ```
  record EventId(String value) {}   // equals/hashCode for free; a plain class must define them
  Map<Topic, Map<EntityId, Integer>> cursors;
  ```
- **When** you see `Map<K, Map<K, V>>` of domain data. **Do** find and name the missing type (`BalanceMap`, `PaymentGraph`). It is the home for invariants and testable on its own. [L47, L68, L90]
- **When** a map is keyed by an entity but only identity matters. **Do** key by id. Tests can then pass strings, and mutable-entity hashCode bugs disappear. [L49, L50]

### Deliberate denormalisation
- **When** the child often needs its parent. **Do** store the parent id on the child (`Expense.groupId`) even though it breaks 3NF. **Because** it serves a frequent read; the instructor calls this normal in production. One write path updates both sides. [L43]
- **When** a cached entity refers to other entities. **Do** store ids, not embedded objects (`Group.userIds`). **Because** embedded objects bloat the cache and go stale. [L47]
- Normal-form target in practice: 2NF, at most 3NF. [L92]

### Derived vs stored state
- **When** a flag can be computed from other state (has the pawn moved; is the game timed). **Do** derive it, inside the object or its factory. **Because** fewer fields means fewer ways to disagree, and callers cannot pass inconsistent combinations. [L34, L82]
- Live-dependent values (portfolio current value) are computed from current prices; store only what writes change (quantity, average price). [L87]
- **When** an aggregate over many records is needed (group balance). **Do** compute it as a read-time fold into the honest type and cache it with invalidation on writes. The instructor first returned a synthetic `Expense`, then corrected it to `BalanceMap`: a sum of expenses is not an expense. [L42, L45, L46, L47]
- Check entity invariants (expense balances sum to zero) on create and edit. [L43]
- "Not yet set" needs an explicit sentinel or Optional; a default 0 end time printed a running process as finished. [L83]

---

## 2. Storage and schema

### The governing rule
**What you store comes from the product features; how you store it comes from the access patterns.** List features as a user would, turn them into APIs and objects, map objects to tables, then write the actual SQL each API runs and shape tables and indexes for it. One table when you read things together; split when you read subsets separately. **Flips when** tuning an existing schema: start from the DBA view. [L92]

### Join tables, not lists in columns
- An array column serves one access direction, rewrites the row per add, keeps stale entries, and makes unrelated writes contend for one row lock (a profile-picture update blocks event access). Relation attributes (RSVP, role) go on the join table. **Flips when** only one direction is ever queried; then an embedded list on that side is defensible. [L86, L92]
- Index `(org_id, user_id)` for "is X a member" and `(user_id)` for "my orgs". Pick composite order by the hot query. [L92]
- Hot, large subset (admins): separate table or composite index leading with the type; a query generally uses one index. [L92]
- Per-user usage limits: a usage row per (coupon, user), not a counter on the shared coupon. [L91]

### Indexes outside rule blobs
- **When** rules are stored as JSON/DSL. **Do** keep discovery metadata (validFrom/validTill, nullable userId, nullable restaurantId, isPlatform, paymentMethod) as indexed columns; union three fetches (user, restaurant, platform), then run the full engine. **Because** searching inside blobs is slow. **Reviewer check:** metadata cannot drift from rules; a restaurant-scoped rule with null `restaurantId` never appears. Unknown rule types fail closed; version the rule schema. [L91]

### Soft deletes and append-only history
- Settling keeps the original record: add a `settled` flag and filter it in every balance query (a missed `WHERE settled = false` gives silently wrong totals). [L42, L43]
- Event logs forbid update and delete; a correction is a new event that references the old id. Essential for ledgers and audits. [L61, L70]
- Delete/flush on a queue: a per-message deleted flag (for everyone) or advance one subscriber's offset (for one); often do not offer it. **Because** hard deletes lose the evidence that a subscriber never got the event. [L90]

### Content addressing
- Key blobs by content hash (SHA-256), bytes in object storage, `hash -> location` row in the DB. Directories are immutable objects listing child hashes; a change rebuilds only the path to the root. Branches are a ref table `(project, branch) -> commit`. **Because** reads dominate; dedup and cache-forever come free. **Flips when** RDBMS only: bytes in a blob column. Costs: orphan GC, full copies unless delta-packed. [L92]
- One query per tree level? First ask which reads need the whole tree; clone is rare and can be bulk. [L92]

### Blueprints for recurring data
- Store rule (restricted cron, not a list of weekdays, which cannot say "third Friday") + first start + optional end. Expand per query window and jump to the window (doubling then binary search, or arithmetic) instead of stepping from the series start. Cap expansion per request. [L86]
- Edit "this and following": end the old blueprint at the split, clone a new one with the patch. Edit one occurrence: end, one-off, clone after. O(1) writes per edit, one notification per series change. Prototype for the clone, Builder for partial patches. [L86]

### ACL tuples
- Store `(subject, relation, object)`; index by subject or object depending on whether "what can X access" or "who can access Z" dominates (both, if both are hot). Not roles in code (`if user.isAdmin`). Start with flat user-object-level rows; add Zanzibar-style usersets only when team/org inheritance is real (the instructor chose flat for GitHub). Short-lived elevation: a signed, expiring token, no DB hit. [L92]

### Client-generated ids and idempotency
- **When** creates can be retried. **Do** let the client mint the id (or an idempotency key) so a resend of "create 123" returns the existing resource. Business fields are not unique enough to dedupe. Compose ids to avoid collisions (user id + timestamp + random, or Snowflake); minted once, never changed. **Flips when** collisions are a real risk: server ids, and lose free idempotency. [L86]
- Event publish is idempotent on producer-assigned event id; the seen-id set needs a TTL. [L61]

---

## 3. API design

### Signatures
- **Accept general, return specific.** Take the most general type the method needs; return the most specific type it produces. Supertype callers still work and subtype-aware callers avoid casts. [L31]
- **Prefer a type parameter over casts or base-interface bloat.** Do not add a method to a base interface so callers can skip a cast (`Board.getSymbol(i, j)`) unless every plausible subtype can honour it (chess, hex, 3D boards cannot; that is an LSP break). Use `Rule<TicTacToeBoard>` so the compiler carries the constraint. [L23]
- **One context object.** When many rules or strategies share an input, pass one request type (`CouponRequest{proposed, cart, applied}`); derive user and restaurant from the cart rather than accepting duplicates that can disagree. [L91]
- Pass whole domain objects, not loose field bags; store only what the algorithm reads (a sliding window keeps timestamps, not requests); prefer neutral names (an opaque limiter `key`, composed as `userId_date` for custom rules). [L73, L74, L76, L87]

### Futures for IO
- **When** a method does a DB write or remote call. **Do** return `CompletableFuture<T>` (`<Void>` for writes with no payload), even with one caller today. **Because** the signature announces latency and failure, and the caller is usually the request-reading thread. Chain with `...Async(fn, executor)`; never `.get()`/`.join()` in a controller; attach failure handlers. **Flips when** the call is local and cheap, or must be sync by design (`boolean canAccept`). JS: a Promise; Go: return a value, the caller picks a goroutine. [L73, L75, L76, L79]

### One entry point vs many methods
- **When** N methods differ only by the target's concrete type (`commentOnTweet`, `commentOnComment`, soon `commentOnReel`). **Do** collapse to one method on a capability type (`comment(Commentable target, ...)`). [L89]
- **When** a "feature" is an update in disguise (RSVP, invite). **Do** fold it into the existing update API; the calendar ended with three APIs. [L86]
- **When** a client exposes many methods but one business decision. **Do** route all of them through one `shouldAccept` that alone calls the algorithm. [L73]
- **When** one logical write touches several structures. **Do** funnel every caller through one private method (`addEventToBus`). [L68]
- **When** an operation is read-then-act across an object boundary (get offset, fetch, bump). **Do** make it one method on the owner (`topic.getNext(sub)`). [L90]

### Capability base types: abstract class or interface
- Shared state or method body (reaction list) -> abstract class; signature only -> interface. Inherit from interfaces by default; class inheritance only for real shared implementation. Single inheritance blocks `Reactable` + `Commentable` together; use interfaces plus composed holders (inferred; the lesson left it open). [L46, L82, L89]

### Authorisation at the owning service
- **When** a read is scoped to a shared resource. **Do** take the caller id with the resource id and check membership in the service that owns the resource, before any downstream fetch. **Because** unauthorised calls then cost and leak nothing. An unchecked `userId` parameter is a smell. [L46, L47]
- Never accept server-owned values from the client: market price comes from server state, `createdAt` is set by the service. [L87, L89]
- Fetch other services' data through their APIs, never their tables. [L46]

### Expose only what clients need
- Expose user actions (place order, get portfolio, watchlist); never internal steps such as exchange execution. [L87]
- Push is an internal effect of `add`, not a public API; expose `add`, `registerPushSubscriber`, `poll`. Publishers only append; the bus assigns positions. [L70, L90]
- Keep cursors server-side so clients only name the topic. **Flips when** clients reliably persist a subscription handle. [L67, L90]
- Read-only APIs (range reads for audit) must not move cursors. [L70]
- Encapsulate: `topic.addMessage(m)`, not `topic.getMessages().add(m)`; `board.setPiece(...)`, not `getCell().setPiece()`; return copies or read-only views. A compile error after hiding a field means the boundary works; add an accessor, do not widen visibility. [L4, L82, L90]

### Versioning via interfaces
- **When** an operation will have several implementations or versions (SMS vs email notifier, service v1/v2). **Do** put it behind an interface. **Because** callers bind to one stable method while implementations change. [L85, L87]

### Layering: gateway -> controller -> DAO
| Layer | Owns | Must not |
|---|---|---|
| Gateway / dispatch | Socket read, deserialise JSON/protobuf to typed requests, hand off to a bounded executor | Business logic |
| Controller / service | Business flow, authorisation, composing futures | Thread pools, SQL, parsing |
| DAO (per table) | All SQL for a table, shared by every controller; returns futures; owns the IO pool | Business rules |
| Models / requests / responses | Internal state vs wire contracts, in separate packages | Behaviour that belongs in services |

Reviewer checks: no SQL outside `dao`; a controller's DAO fields show which tables it touches; the event loop never awaits IO; executors are bounded; request id flows into the response. [L4, L74, L75, L76, L87]

---

## 4. Choosing data structures from operations

List every operation with the cost of each internal step; judge the design by its worst API, on paper before coding. [L70, L83]

| Operation needed | Structure | Cost | Refs |
|---|---|---|---|
| Exact lookup by id, update by key | Hash map (`ConcurrentHashMap` under threads) | O(1) | L68, L70, L87 |
| "First after T", floor/ceiling, range | Sorted map (`TreeMap`; `ConcurrentSkipListMap` under threads) | O(log n) seek + O(k) scan | L67, L70 |
| Repeatedly take max/min, reinsert remainder | Heap (`PriorityQueue` with comparator) | O(log n) per op | L44, L48, L83 |
| Lookup by id AND earliest by time | Two indexes over the same objects | O(1) / O(log n) | L83 |
| Window on an append-only, time-ordered list | Binary search on timestamp | O(log n) | L89 |
| Per-consumer position | Cursor map (topic, consumer) -> index | O(1) | L67, L70, L90 |

- **Hash vs sorted.** A hash map returns null for keys not stored, so it cannot answer "nearest timestamp". `TreeMap` is a red-black tree: O(log n), never claim O(1). [L70, L83]
- **Two indexes over the same objects.** Map `id -> obj` plus a heap/tree on the order key. Sort on the key the query needs (a TreeMap keyed by process id returned the smallest id, not the oldest process). Mutating a non-key field via the map is O(1) and visible to the queue; changing the sort key needs remove and re-insert. Each concurrent structure is safe alone; the pair needs one lock for mutate/delete. [L83, L84]
  ```
  Map<String, Process> byId;               // end(id): O(1), sets p.end
  PriorityQueue<Process> byStart;          // poll(): O(log n), by (start, id)
  void start(String id) { Process p = new Process(id, clock.now());
    byId.put(id, p); byStart.add(p); }     // both indexes, one place
  ```
- **Heaps.** Greedy settlement: max-heap of creditors, max-heap of debtors by magnitude; pair the tops, push back the remainder. O(n log n), at most n-1 edges, but a heuristic, not optimal (creditors {80, 25} vs debtors {20,20,20,20,25}: optimum 5, greedy 6). Java's `PriorityQueue` is a min-heap; reverse the comparator deliberately. [L44, L48]
- **Skip lists.** `ConcurrentSkipListMap` is the JDK's concurrent sorted map (`TreeMap` is not thread-safe); used for per-topic `timestamp -> index`. [L67, L70]
- **Pitfalls.** A plain timestamp key overwrites ties: use (ts, seq) or `putIfAbsent`. Assign timestamps inside the component so index order matches list order. Create nested maps atomically (`computeIfAbsent`). Ship an O(n) scan if needed, mark it, and say how you would index it. [L66, L67, L70, L83]

---

## Interview-only notes
- Name CRUD and mock storage with in-memory maps; spend the code on the algorithm and the orchestration path. [L45, L46, L47]
- State choices out loud with the trade-off (access patterns, contention, normalisation); explaining it is what gets scored. [L86]
