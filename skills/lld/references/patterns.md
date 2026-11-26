# Design patterns: when to use, when to reject

Use this when you are about to introduce (or are reviewing) a design pattern: picking one for a requirement, deciding whether a pattern in a PR earns its place, or choosing between two that look alike. Start at the picker, jump to the entry, check "Don't use when" before writing code.

**Contents:** [Picker](#picker) · [Ground rules](#ground-rules) · [Creational](#creational) · [Structural](#structural) · [Behavioural](#behavioural) · [Concurrency-shaped](#concurrency-shaped-patterns) · [Confusable pairs](#confusable-pairs) · [Tried and reverted](#tried-and-reverted) · [Interview-only notes](#interview-only-notes)

## Picker

| Signal you see in code or requirements | Pattern | Rejected alternative (and why) |
|---|---|---|
| Code tries hypothetical changes (AI lookahead, dry run, "does this leave my king in check") on live state | Prototype (`copy()` / copy-returning `move`) | Make/undo on one object: undo cascades in rich domains, unsafe when concurrent [L12, L13, L82] |
| Adding one optional field forces more constructor overloads; callers pass `null`/`false`/`0` placeholders | Builder | Telescoping constructors, one full constructor with placeholders [L19] |
| Construction needs defaults, derived flags or fresh collaborators; tests repeat a 6-line setup | Factory | Builder (problem is logic, not many optional fields); condensing to one line [L34, L35] |
| Stateless handler/strategy re-instantiated on every call | Singleton (via DI scope) | `new Successor()` per call; hand-rolled lazy init in prod [L25, L26] |
| Many concurrent requests need an expensive, capped resource (connections, notifier clients) | Object/resource pool | Create per request; semaphores; a single FIFO queue [L94] |
| Many identical immutable value objects (`new Cell(r,c)` everywhere) | Flyweight / interning cache | `new` everywhere; `Set<Cell>` lookup per call [L35] |
| Many heavy snapshots kept, rarely read | Compact representation + rebuild constructor | Transparent Proxy (memory creeps back) [L30] |
| Heavy resource that callers must use unchanged but may never touch | Virtual Proxy | Eager construction [L30] |
| Method can legitimately return nothing | `Optional<T>` or a neutral domain object | Raw `null` [L16, L25, L26] |
| Two loops identical except traversal order | Traversal function (`(i,j) -> cell`); Iterator only for 1-D walks | Iterator for 2-D scans: needs two iterators [L14, L15] |
| Same operation, different algorithm chosen by input/config (buy vs sell, token bucket vs sliding window) | Strategy | Separate public methods per algorithm; if/else or `switch` [L11, L32, L73, L87] |
| Branches look like phases (opening, middlegame) | Usually a selector + Strategy, not State | State: dense transitions from global data [L32] |
| "Try A, else B, else C" with fixed priority, list keeps growing | Chain of Responsibility | Rule set (loses order); nested fallback helpers; one big method [L24, L26] |
| Sequence of independent, order-free checks; each new feature edits the same function | Rule engine / rule list | Growing if-chain; wrapper "onion" types [L17, L18, L91] |
| Subclasses share fixed steps around a varying step | Template method (abstract class) | Interface (cannot hold shared steps); `type` field with branching [L82] |
| Undo/redo where one action cascades | Memento (snapshots) | Inverse operations [L29] |
| Service method with a growing positional parameter list and many callers | Command (+ Builder) | Overloads per email type; one mega-method [L39] |
| Publisher calls each consumer directly; consumers added/removed over time | Observer / event bus | Direct calls; polling loop with sleep [L41, L87, L94] |
| Per-entity ordering needed, global ordering not | Keyed executor | One thread; plain pool; thread per key [L55, L63, L65] |
| Flaky dependency; retry spacing may vary per caller | Retry strategy | Fixed sleep baked into the caller [L64] |

## Ground rules

- **Pattern only on pain.** Add a pattern when a concrete change request makes current code hard to extend, not because a name fits [L0, L14, L87].
- **Classify before refactoring.** Who picks the behaviour: the input (Strategy), a phase graph (State), a fixed priority (Chain), or nobody (rule list)? [L32, L24]
- **Build one class first**, including its hardest method (`next()`), and revert if the original smell survives anywhere [L32].
- **Compose deliberately** (Chain + Singleton + Optional [L25]; Command + Builder [L39]) and name only what you did: a shared base class is not a factory [L89].

---

## Creational

### Prototype
- **Use when:** code evaluates hypothetical changes against a stateful object; an operation derives a new T from a T (`player.flip()`, `board.move(m)`); a recurring series is split on edit (`blueprint.cloneFrom(t)`) [L12, L13, L37, L82, L86].
- **Don't use when:** state is huge, search is single-threaded and hot, and undo is trivial (clear one cell). Then make/undo on one instance is cheaper [L12, L13].
- **Shape:**
  ```java
  interface Board { Board copy(); Board apply(Move m); }
  final class GridBoard implements Board {
    private final String[][] cells;
    public GridBoard copy() {
      String[][] c = new String[n][n];
      for (int r = 0; r < n; r++) c[r] = cells[r].clone(); // safe: Strings immutable
      return new GridBoard(c);
    }
    public GridBoard apply(Move m) { GridBoard b = copy(); b.place(m); return b; }
  }
  // caller MUST reassign: board = board.apply(m);
  ```
- **Pitfalls hit:** shallow copy is safe only if referenced objects are immutable or only ever replaced; a dropped return value is a silent no-op, so pick copy-returning or in-place and stick to it; returning the opponent's simulated move instead of your own [L12, L13, L37].
- **Production:** what-if pricing, dry runs, simulation. Reviewer: every copy-returning call reassigned; no shared mutable field in the copy [L13, L37].

### Builder
- **Use when:** overloads grow combinatorially as optional fields arrive; call sites pass placeholders; a command/DTO has many optional fields; clients send partial update payloads [L19, L24, L39, L86].
- **Don't use when:** the difficulty is initialisation logic or defaults (use Factory) [L34]; there is one parameter and one way to build (use a constructor) [L41].
- **Shape:**
  ```java
  final class Report { /* final fields */ Report(Builder b) { ... } }
  static final class Builder {
    private boolean done; private String owner; private int retries = 3; // defaults here
    Builder done(boolean v)   { done = v;   return this; }
    Builder owner(String v)   { owner = v;  return this; }
    Report build() {
      if (owner == null) throw new IllegalStateException("owner required");
      return new Report(this);
    }
  }
  ```
- **Pitfalls hit:** forgetting `build()`; nothing enforces required fields unless `build()` validates (inferred); an abstract base builder returns the base type, so the consumer needing the subtype fails to compile. Fix with composition (each concrete builder holds a shared details-builder) rather than casts or `buildEmail()/buildSms()` on the base [L19, L40, L41].
- **Production:** DTOs, SDK options, test data builders; prefer named/default args where the language has them (inferred). Reviewer: required fields checked, product immutable [L19]. Payoff seen: a later field touched only builder and product [L24].

### Factory
- **Use when:** construction needs starting state the caller should not choose (null winner, zero elapsed, fresh board), derived flags (timed iff a limit is set), or creation-time business checks (profile exists, not already in a game) [L34, L35].
- **Don't use when:** parameters are all independent optional fields with no derivation (Builder) [L34]; nothing varies in construction [L89].
- **Shape:**
  ```java
  class GameFactory {
    Game timed(Integer perMoveMs, Integer perPlayerMs) {
      boolean timed = perMoveMs != null || perPlayerMs != null; // derived, not asked
      return new Game(new Config(timed, perMoveMs, perPlayerMs), new GridBoard());
    }
    Game timed(int perPlayerMs) { return timed(null, perPlayerMs); }  // defaults inside
    Game casual()               { return timed(null, null); }
    Game fromPosition(Board b)  { /* separate intent for analysis */ }
  }
  ```
- **Pitfalls hit:** primitive `int` for a nullable limit unboxed to NPE (use boxed/Optional); the factory filled the "absent" limit with a wrong value, so the game took the wrong branch. Unit-test the factory separately from game logic [L34, L37].
- **Production:** `OrderFactory.newCartOrder(...)`; tests build fixtures through the same factory. Reviewer: literal nulls into constructors, derivable flags passed in, one god-method with nullable params [L34, L35].

### Singleton
- **Use when:** a stateless handler, strategy or rule is re-created repeatedly; an injectable `Timer` shared in production [L25, L26, L64].
- **Don't use when:** the object holds per-request mutable state; the object is copied for simulation (the chess class suggested a singleton board, which conflicts with temp-board validation and multiple games: treat as not advisable) [L25, L82].
- **Shape (prefer DI scope; hand-rolled only when asked):**
  ```java
  @Singleton class DefendStep implements Step { ... }          // Guice/Spring/Dagger
  // hand-rolled, interview only:
  final class DefendStep implements Step {
    private DefendStep() {}
    private static class Holder { static final DefendStep I = new DefendStep(); }
    static DefendStep get() { return Holder.I; }               // lazy, thread-safe
  }
  ```
- **Pitfalls hit:** public constructor left in; `static` getter cannot be forced via an interface; an abstract base cannot hold the boilerplate; a `getIfNull(instance, Supplier)` helper that does not assign back never caches; `synchronized` dropped in refactor [L25, L26]. The holder idiom is the standard fix (inferred).
- **Production:** singleton-scoped beans for stateless validators and filters. A mutable field on a shared bean is a race; static singletons block test fakes [L25, L26].

### Object pool
- **Use when:** many concurrent workers contend for an expensive, mutable resource whose count must be capped (notification senders, DB/HTTP clients) [L94].
- **Don't use when:** the objects are immutable values (that is interning, below) [L35, inferred].
- **Shape:**
  ```java
  class SenderPool {
    private final BlockingQueue<Sender> idle; private final AtomicInteger made; private final int max;
    Sender acquire() throws InterruptedException {
      Sender s = idle.poll();
      if (s != null) return s;
      if (made.incrementAndGet() <= max) return Sender.open();
      made.decrementAndGet(); return idle.take();             // wait for a release
    }
    void release(Sender s) { idle.offer(s); }                 // in finally
  }
  ```
- **Pitfalls:** not releasing on error paths, no acquisition timeout. The interviewer wanted a pool, not semaphores or a FIFO queue [L94].

### Flyweight / interning
- **Use when:** many identical immutable values from a small bounded key space [L35].
- **Shape:**
  ```java
  final class Cell {
    private static final Cell[][] CACHE = new Cell[N][N];
    static { for (int r = 0; r < N; r++) for (int c = 0; c < N; c++) CACHE[r][c] = new Cell(r, c); }
    private Cell(int r, int c) { ... }
    static Cell of(int r, int c) { return CACHE[r][c]; }
  }
  ```
- **Pitfalls hit:** accessor and cache must both be static; `Set<Cell>` lookup costs too much per call (use an array); hand-written 3x3 init breaks for NxN; unlocked lazy init is unsafe (inferred) [L35].
- **Naming:** the course calls it an object pool; for immutable shared values the standard name is flyweight/interning (inferred).

## Structural

### Proxy
- **Use when:** callers must keep using the real interface unchanged, and the real object is expensive and may never be needed (DB connection, heavy resource): build it lazily on first use [L30].
- **Don't use when:** low memory is the hard requirement: any call can rebuild and keep the full object. Store a compact representation plus a rebuild constructor on the real class (the course's choice for undo history) [L30].
- **Shape (virtual proxy):**
  ```java
  class LazyBoard implements Board {
    private final String encoded; private Board real;
    LazyBoard(String encoded) { this.encoded = encoded; }
    private Board real() { if (real == null) real = GridBoard.decode(encoded); return real; }
    public Board apply(Move m) { return real().apply(m); }   // every method delegates
  }
  ```
- **Pitfalls:** every method must be re-delegated; decide whether the built object is kept; lazy build not thread-safe (inferred). Test a lossless round trip [L30].

### Null object / Optional
- **Use when:** "no result" is a legitimate outcome (rule did not fire, lookup missed, no streak) [L16, L25, L26].
- **Do:** return `Optional<T>` for lookups/handlers, or a neutral domain value (`GameState.NONE`, `ValidationResult.ok()`), then delete the now-dead `!= null` checks [L16, L25]. Also: default strategy when the caller passes `null` (sliding window if no algorithm given); a no-op default callback [L71, L78].
- **Don't:** use `Optional` for fields or parameters (inferred); use it on an allocation-sensitive hot path (inferred) [L25]. For "must exist" lookups, throw a specific domain exception instead [L66].
- **Pitfall hit:** a wrapper whose getter returned `null` crashed the engine; a wrapper's job is to guarantee non-null [L23].

### Composite
Not taught as a pattern. The coupon engine ANDs a flat rule list and defers OR/nested logic as "more complex"; a composite rule tree (`And(rules)`, `Or(rules)`, `Not(rule)` each implementing `Rule`) is the natural next step (inferred) [L91].

## Behavioural

### Iterator
- **Use when:** the walk is a single sequence; callers should not see indices; the walk shape is irregular (zigzag, spiral) or will change [L15].
- **Don't use when:** the scan is 2-D (line starts x cells in line). One iterator per dimension makes it wordier than a traversal function [L15].
- **Shape (what the course kept):**
  ```java
  GameState streak(IntFunction<String> at) {      // i -> symbol along one line
    String first = at.apply(0);
    if (first == null) return GameState.NONE;
    for (int i = 1; i < n; i++) if (!first.equals(at.apply(i))) return GameState.NONE;
    return GameState.won(first);
  }
  // rows: for r: streak(i -> b.symbol(r, i)); diag: streak(i -> b.symbol(i, i))
  ```
- **Pitfalls hit:** one generic traversal is rigid: a new shape will not fit [L15]; index-heavy lambdas need domain names [L14]. A precomputed list of lines generalises to NxN and odd shapes (inferred).

### Strategy
- **Use when:** the same operation has several algorithms and the **input or config** picks one (difficulty setting, buy vs sell, rate-limit algorithm per service, retry policy per destination); strategies are isolated and never hand off to each other [L11, L32, L73, L78, L87].
- **Don't use when:** the programmer, not the input, would choose, and the choice depends on changing context mid-run; put one selector in one place [L32]. Don't expose one public method per algorithm: keep one entry point and select internally [L11].
- **Shape:**
  ```java
  interface OrderExecution { Result place(User u, Stock s, int qty, long limitPrice); }
  class BuyExecution  implements OrderExecution { /* check funds, debit, execute, add holding */ }
  class SellExecution implements OrderExecution { /* check holdings, execute, remove, credit */ }
  class RateLimiterClient {
    private final Algorithm algo;
    RateLimiterClient(Algorithm a, Config c) { algo = (a != null) ? a : new SlidingWindow(c); }
  }
  ```
- **Pitfalls:** strategy and callback sharing mutable state (back pressure counter) couples them and needs thread-safe counters [L73]; a strategy taking a concrete type should take the narrowest capability interface [L25, L28].
- **Production:** payment providers, channels, rate-limit and retry policies; tiers as a policy held by the entity, not `ProAccount extends Account` [L21]. Test the selector apart from each strategy [L11].

### State (rejected in the course)
- **Tried on:** AI move selection by game phase (opening, middle, time pressure, optimal) [L32].
- **Why rejected:** writing `next()` for the first state needed the same global if/else (board, clock, move count), so transition logic would be copied into every state; the graph was a near full mesh (5 states, ~25 edges); the "state" was really unbounded data (positions x clock values); the nested condition remained [L32].
- **Test before using:** draw states as nodes and transitions as edges. Sparse, event-driven exits from a finite named set -> State fits. Dense or context-computed -> a selector plus Strategy [L32].
- **Good fits:** order lifecycle, connection states [L32]; even for order status the course uses an enum plus an append-only log [L94]. `switch` instead of if/else is not a fix [L32].

### Chain of Responsibility
- **Use when:** "try A; if nothing, try B; then C" with a fixed priority and new steps keep arriving (AI placement: win, block, fork, centre, corner) [L24, L26].
- **Don't use when:** the steps are independent and order-free (rule list); the list is short and stable, or readers need the whole flow at a glance: tracing a chain across classes is tedious [L26].
- **Shape:**
  ```java
  interface Step { Optional<Cell> pick(GridBoard b, Player p); Step next(); } // null = end
  Move choose(GridBoard b, Player p) {
    for (Step s = WinStep.get(); s != null; s = s.next()) {   // loop on s, not s.next()
      Optional<Cell> c = s.pick(b, p);
      if (c.isPresent()) return new Move(c.get(), p);
    }
    throw new IllegalStateException("no step produced a move");
  }
  ```
- **Pitfalls hit:** head wired to the wrong handler; looping on `next() != null` skipped the last handler [L26].
- **Flips when:** order must be configurable at runtime: build an ordered list in one place (inferred) [L26].
- **Production:** pricing fallbacks, filters, cache-then-DB-then-remote, provider A else B. Reviewer: head matches spec, no cycles, tail runs, handlers stateless; one golden test asserts the order [L26].

### Rule engine / rule list
- **Use when:** a function is a series of independent checks, each able to return early, and every feature edits that function (win by row/col/diagonal; coupon eligibility set by non-engineers; validators) [L17, L18, L20, L85, L91].
- **Don't use when:** rules are order-dependent or config-dependent (timer variants): someone turns the list into a set and logic silently breaks; keep explicit if/else with named branch methods [L22, L24].
- **Shape:**
  ```java
  interface Rule { Verdict check(Context ctx); }                 // rich result, not boolean
  final class RuleEngine {
    Verdict all(List<Rule> rules, Context ctx) {
      for (Rule r : rules) { Verdict v = r.check(ctx); if (!v.ok()) return v; } // AND
      return Verdict.OK;
    }
  }
  // rules supplied per type/tenant: Map<Class<?>, RuleSet>, or loaded from DB via a type registry
  ```
- **Pitfalls hit:** boolean rule lost the winner; first-match loops make order matter anyway (draw rule last); `getRules()` returned null [L18, L23].
- **Production:** coupons, discounts, fraud. Store rules as JSON with a type tag and deserialize through a registry; put searchable metadata (validity, userId, restaurantId, platform flag) in indexed columns, never search rule blobs; keep a few developer-written "system coupons" for bespoke cases [L91].
- **Wrapping is not extension:** `GameInfo` around `GameState` worked once, then each new request repeats the question ("onion") [L17, L20].

### Template method
- **Use when:** subtypes share fixed steps around one varying step (chess `move`: reject own-colour capture, simulate on a copy, reject if own king in check, then piece-specific `isValidMove`) [L82].
- **Shape:**
  ```java
  abstract class Piece {
    final boolean move(Position to) {
      if (!legal(to)) return false;          // shared steps
      board.relocate(this, to); return true;
    }
    private boolean legal(Position to) { /* own-capture, king-safety via board.copy() */ return reaches(to); }
    protected abstract boolean reaches(Position to);   // per piece
  }
  ```
- **Pitfalls hit:** started as an interface, switched to abstract class once shared logic appeared; a `type` check in the shared method contradicted inheritance [L82].

### Memento
- **Use when:** undo/replay is required and one action can mutate a large, hard-to-predict part of state (cascades, chain reactions) [L29].
- **Don't use when:** state is large and actions small and cleanly invertible: store inverse ops or a command log (inferred); tic-tac-toe undo can just clear the cell, or replay the move log [L29, L93].
- **Shape:**
  ```java
  class History {
    private final Deque<String> snaps = new ArrayDeque<>();   // compact form, not live boards
    void save(GridBoard b) { snaps.push(b.encode()); }
    GridBoard undo() {
      if (snaps.isEmpty()) throw new IllegalStateException("nothing to undo");
      return GridBoard.decode(snaps.pop());
    }
  }
  ```
- **Pitfalls hit:** remove-while-indexing shift; callers made clones while the board owned history (split ownership misses states); live snapshots too heavy, hence the compact form [L29, L30].

### Command
- **Use when:** a shared service method has a growing positional parameter list with many callers; you want one `execute(cmd)` entry and the option to queue the request later [L39, L40].
- **Don't use when:** one call site with a stable 2-arg signature [L39].
- **Shape:**
  ```java
  final class SendEmail { final User to; final String templateId; final Map<String,String> vars; ... }
  class EmailService {
    void execute(SendEmail c) { deliver(c.to, fill(c.templateId, c.vars)); } // only sends
  }
  // what to send (region link, template) lives in the command's builder, not caller or sender
  emailService.execute(SendEmail.builder().to(u).template("WIN").build());
  ```
- **Split roles:** caller invokes, command describes, service performs [L39]. Event-to-channel mapping goes in the channel command's constructor, not `event.toEmail()` [L41].
- **Reviewer:** channel calls with more than 3 positional args; `if country == ...` inside the sender [L39].

### Observer and pub-sub / event bus
- **Use when:** a publisher has **multiple consumer types that can be added or removed** (order status -> SMS, invoice, refund-on-cancel; game win -> email, SMS) [L41, L87, L94].
- **Don't use when:** there is one fixed recipient ("notify the user who placed this order"): nothing subscribes or unsubscribes [L87]; the class that changes the status would observe itself [L94].
- **Shape:**
  ```java
  interface OrderListener { void onStatus(Order o, Status s); }
  class OrderEvents {
    private final List<OrderListener> ls = new CopyOnWriteArrayList<>();
    void add(OrderListener l) { ls.add(l); }  void remove(OrderListener l) { ls.remove(l); }
    void publish(Order o, Status s) {
      for (OrderListener l : ls) try { l.onStatus(o, s); } catch (RuntimeException e) { log(e); }
    }
  }
  ```
- **Rejected:** direct calls to each service; consumers polling a public list with sleep; event subclasses (flattened to one `Event` with a `type`) [L41].
- **Pitfalls (inferred):** under synchronous dispatch one throwing subscriber stops the rest and a slow one blocks the publisher [L41, L94].
- **Production:** in one service, Observer; across services, outbox + broker. At bus scale: topics, push as a side effect of `add`, typed `Subscription` with filter, retry then DLQ [L60, L66, L90]; see concurrency-and-async.md.
- **Instructor changed mind:** resisted Observer for notifications, then accepted it for multi-service fan-out [L87].

## Concurrency-shaped patterns

### Keyed executor
- **Use when:** operations on the same key must stay ordered (read-your-writes in a cache, per-topic append, per-process start/end) but different keys may run in parallel [L55, L58, L62, L65, L84].
- **Rejected:** one thread (ordered, slow); plain pool (fast, unordered: a same-key read can overtake the write); thread per key (millions of threads); a thread class inside the domain class [L55, L63, L65].
- **Shape:**
  ```java
  final class KeyedExecutor {
    private final ExecutorService[] lanes;              // each newSingleThreadExecutor(), size from config
    <T> CompletableFuture<T> submit(Object key, Supplier<T> task) {
      return CompletableFuture.supplyAsync(task, lanes[Math.floorMod(key.hashCode(), lanes.length)]);
    }
  }
  ```
- **Key choice:** hash the narrowest key that carries the guarantee: (subscriber, topic) for reads, topic for total order per topic [L62, L65, L68].
- **Pitfalls (inferred):** negative `hashCode` (use `floorMod`); head-of-line blocking within a lane; resizing remaps keys and breaks in-flight order; `thenApply` callbacks run off the lane [L55, L59, L63].
- Details: concurrency-and-async.md.

### Retry strategy
- **Use when:** a component redoes failing work and the spacing policy varies (exponential vs periodic) per destination [L61, L64].
- **Shape:**
  ```java
  abstract class Retry {
    final int max; final Timer timer;                    // Timer injected; fake in tests
    abstract long waitMs(int attempt);                   // Exponential: base * 2^(attempt-1)
    <P,R> R run(Function<P,R> task, P arg) {
      for (int a = 1; ; a++) {
        try { return task.apply(arg); }
        catch (RetryableException e) { if (a >= max) throw new RetryLimitExceeded(e); timer.sleep(waitMs(a)); }
      }
    }
  }
  ```
- **Decisions:** retry only a caller-declared retryable type; distinct limit-exceeded error; wait from attempt number, not a mutating factor; config-injected limits; DLQ after the last attempt [L64, L68].
- **Don't:** auto-retry financial operations on business failures [L87].
- **Pitfalls (inferred):** no jitter or cap; non-idempotent side effects duplicated; `sleep` on a keyed lane stalls that key [L64]. A loop is shown here; the course used recursion bounded by max attempts.

## Confusable pairs

| Pair | Distinguish by |
|---|---|
| Strategy vs Observer (Zerodha class) | Strategy picks **one** algorithm from a family for the same call (buy or sell). Observer **fans out** one event to **many** consumers whose set changes at runtime. One fixed recipient needs neither [L87]. |
| Proxy vs Singleton | Both control creation; Singleton limits to one instance, Proxy delays a heavy one behind the same interface [L30]. |
| Flyweight vs pool | Immutable shared values vs mutable resources checked out and returned [L35, L94, inferred]. |

## Tried and reverted

| Attempt | Outcome | Ref |
|---|---|---|
| Iterator for 2-D win scan | Back to traversal functions | L15 |
| `GameInfo` wrapper around `GameState` | Kept once, rejected as a strategy -> rule engine | L17, L18 |
| Generics dropped from rules, casts used | Generics restored; later replaced by `CellBoard` capability interface | L23, L27 |
| Transparent Proxy for history | Plain representation + rebuild constructor | L30 |
| State pattern for AI phases | Abandoned after one class | L32 |
| Per-check helpers that each made the move | Logic moved back inline as one predicate | L37 |
| Abstract base command + base builder | Composition with shared details-builder | L40, L41 |
| Builder taking a single event | Constructor | L41 |
| Doubling wait-factor field in retry | Stateless `2^(attempt-1)` | L64 |
| Two maps for push/pull subscribers | One map of typed subscriptions | L66 |
| Board as singleton (chess) | Flagged as conflicting with temp-board copies | L82 |

## Interview-only notes

- Hand-write a singleton only when asked; say you would use a DI scope [L25]. Tie each pattern to the requirement that needs it; reflexive Observer or Factory is a flagged mistake [L87, L89].
- Asked "Chain of Responsibility vs Observer for post-order steps", the instructor did not answer: Chain is for first-match priority, Observer for independent reactions (inferred) [L87].
