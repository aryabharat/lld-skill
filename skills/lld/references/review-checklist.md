# LLD review checklist

Use this when reviewing a design doc, class diagram or PR, or self-checking your own LLD before calling it done. Each item is a yes/no question; a "no" (or "yes" on a smell question) is a finding. Grade with the severity guide, then walk the sections the change touches.

Contents: Severity guide · Scope · Objects and naming · APIs · Extensibility · Patterns · Algorithms and data structures · Concurrency · Resilience · Persistence · Tests

## Severity guide

The course ranks correctness first, then readability and extensibility; polish comes last [L1, L2, L37]. Map findings like this:

| Severity | What falls here | Examples |
|---|---|---|
| **Must-fix** | Wrong results, broken invariants, races, data loss, blocked request threads, unvalidated state mutation | Float money; zero-sum not checked; torn read between two writes; settle deletes history; `.get()`/`join()` on an IO thread; network call in a constructor; retries exhausted and message only logged; occupied cell accepted; index not cleared on overwrite [L43, L45, L54, L68, L79, L58, L93] |
| **Should-fix** | Design that makes the next change an edit of tested code, or hides bugs | `instanceof`/type switch in a generic service; base-class member some subtypes cannot honour; nested `Map<.., Map<..>>` in signatures; raw `null` for "not found"; system clock read inside logic; missing test for an edge rule; pattern named but not matching the code [L3, L5, L23, L25, L33, L89] |
| **Nice-to-have** | Readability and hygiene with no behaviour risk | Abbreviated names; missing `toString`; package layout; typed ID wrappers (may be overkill, say why); formatter not run [L7, L13, L50, L68] |

Escalate a should-fix to must-fix when it sits on a hot path, money, or shared mutable state (inferred). Leaving a known smell is acceptable if it is named with a follow-up [L31].

## Scope

- Is there a written, numbered requirement list with core vs deferred items marked? [L42, L53, L87, L93]
- Was it stated what is actually being stressed (algorithm, concurrency, extensibility) before building? [L50]
- Is every pattern or abstraction justified by a current requirement, and was the simple version considered first? [L0, L28]
- Is the hard, central part built and tested before CRUD, auth and wrappers? [L45, L47, L50]
- Are trivial or out-of-scope parts stubbed on purpose and named as stubs? [L45, L82, L86]

## Objects and naming

- Can each class's purpose be stated without "and"; no bare `Manager`? [L8, L10]
- Does every field define its object, with growing collections moved to their own association or class? [L43, L87]
- Is every field and model class used by some behaviour in the change? [L47, L50]
- Is any stored flag derivable from existing state (then derive it)? [L82]
- Are stable identity and per-session role separate (`User` vs `Player`)? [L22]
- Is per-participant state on the participant, not indexed fields or keyed maps in the parent? [L22]
- Are nested generic types and parallel lists replaced by named classes or one record? [L23, L43, L47]
- Is money an immutable value object with currency and integer minor units? [L43, L44, L48]
- Are domain constants enums (not strings or booleans), and thresholds named and parameterised? [L11, L31, L87]
- Do names say what the value is, and do accessor names match return types? [L12, L24, L47]
- Is there one status as source of truth, with history in an append-only log? [L94]

## APIs

- Do public methods exist for every required flow and name every domain object they take or return? [L3, L43]
- Does a query with more than two outcomes, or one that must report an actor, return a result object or enum, not a boolean? [L3, L18, L93]
- Is each core method's signature and every return value defined before implementation? [L93]
- Does an "assign/find" API own discovery, selection and persistence rather than acting as a setter? [L94]
- Does every mutation pass through an owner method that validates (no `a.getB().setC()`)? [L4, L41, L82, L90]
- Are internal collections hidden behind the owner's API? [L4, L23, L90]
- Is there one public method per capability, not one per algorithm variant (`suggestSmartMove`)? [L11]
- Do methods accept the most general type they need and return the most specific type they produce? [L31]
- Do group-scoped APIs take the caller's id and check authorization before any downstream call? [L46, L47]
- Are server-owned fields (ids, `createdAt`, market price) set by the service, not taken from the request? [L87, L89]
- Are internal models separated from wire request/response types, each endpoint with its own response type? [L75]
- Are optional-heavy constructors replaced by a builder or intent-named factory, with no `null`/`0` placeholders at call sites? [L19, L34]

## Extensibility

- Can the next likely feature be added mostly by adding code, without editing a tested core method? [L0, L17, L20]
- Can a new rule/condition/channel be added without editing the engine or existing consumers? [L18, L28, L40, L91]
- Is the varying policy injected (list, map, strategy) rather than hard-coded? [L20, L56]
- Does any base class or root interface carry a member some plausible subtype cannot honour, or throw "unsupported"? [L5, L23, L27]
- Is there any `instanceof`, type field, downcast or `buildX()` per subtype? [L3, L23, L40, L82]
- Does every `extends` pass a plain-English "X is a Y" test, and is shared code composed rather than inherited for reuse? [L21, L40, L82]
- Is configuration separated from domain state, with old behaviour unchanged under default config? [L21]
- Does a producer avoid importing its consumers, with subscriptions wired in one place? [L41, L60]
- Are collaborators typed at the narrowest interface that supplies the methods used? [L27, L28]

## Patterns

- Does each pattern map to a concrete runtime variability, and does the code actually match the named pattern? [L87, L89]
- State vs Strategy: is the selection in one place, the state set finite, and the transition graph sparse? [L32]
- Prototype/copy: is every mutable field deep-copied, with a test that mutating the copy leaves the original intact? [L13]
- Memento: is snapshotting in one place, future states truncated on rewind, and memory bounded? [L29, L30]
- Singleton: private constructor, thread-safe init (or DI-managed), no mutable shared state unguarded? [L25, L26]
- Chain of responsibility: is priority order explicit and tested, with each handler returning `Optional`? [L24, L26]
- Observer: can a new consumer be added without editing the subject; no self-observation; one slow observer isolated? [L94]
- Pool/flyweight: justified by object cost or volume, bounded, and are shared instances immutable? [L35, L94]

## Algorithms and data structures

- Does each operation have a stated complexity, with no O(n) where O(log n) or O(1) is achievable? [L70, L83]
- Does a terminal check inspect only what the latest change can affect, or use maintained aggregates? [L93]
- Are incremental aggregates updated on every mutation path, including undo, reset and replay? [L93]
- Is there one index per ordering need (expiry vs eviction), all updated in one choke point? [L56, L57, L58, L68]
- Are range, "after T" or "nearest" lookups on a sorted structure, not a hash map? [L67, L70]
- Are sort keys immutable while in a tree/heap, and ties broken deterministically? [L57, L83, L44]
- Is a heuristic documented as such, with a known non-optimal fixture? [L44]
- Are deep nested loops (3+) replaced by named traversals or existing domain operations? [L17, L31]

## Concurrency

- Can any reader observe shared state between two writes of one logical update? [L45]
- Is multi-field state with an invariant swapped atomically as an immutable object, or guarded by one lock? [L45, L84]
- Is ordering defined as a scope (per key/topic/entity) and enforced by routing the key to one single-threaded lane? [L55, L62, L65]
- Is the lane key the narrowest one meeting the guarantee, with a non-negative hash? [L63, L65, L68]
- Can one slow or hot key stall unrelated keys on the same lane? [L62, L63, L65]
- Do request threads avoid all blocking IO, with slow work on a separate bounded executor? [L54, L75, L76]
- Does any constructor perform network IO or block on a future? [L78, L79]
- Do IO methods return futures, completed on success, exception and timeout? [L54, L56, L79]
- Do concurrent misses on one key cause exactly one backend call (request collapsing)? [L53, L59]
- Are lazily initialised shared caches and singletons safe under concurrent access? [L25, L30, L35]
- Are prune-check-append (or read-fetch-advance) atomic per key? [L81, L90]
- Is exclusive-assignment written conditionally so a second worker cannot double-assign? [L94]

## Resilience

- Are failure paths handled, with a fallback where the operation matters? [L1]
- Are retries capped, limited to retryable errors, with backoff behind a policy interface? [L64]
- After retries run out, is the failed message kept in a DLQ rather than only logged? [L61, L68, L90]
- Does every blocking wait have a timeout and defined failure response? [L52, L84]
- Is fail-open vs fail-closed stated for an unreachable dependency? [L72, L74]
- Is "no candidate found" or "missing rule set" an explicit, loud failure? [L18, L94]
- Are non-critical side effects moved off the synchronous critical path? [L73, L94]
- Do stateful objects refuse mutations once terminal? [L36, L37]
- Is publish idempotent on event id, and are retried operations idempotent? [L61, L64]

## Persistence

- Is the write policy (write-through/back) stated, and write-back data-loss risk bounded? [L51, L56]
- In write-through, is memory updated only after persist succeeds? [L56, L59]
- Does settle/delete keep history as a state change? [L42, L43]
- Are list-valued attributes rows in a junction table, each index justified by a named query? [L86, L92]
- Does each service read only its own tables? [L46, L76]
- Is a status write paired with its log append in one transaction? [L94]
- Is publish acknowledged after durable write, with offsets restored on restart? [L90]

## Tests

- Does a runnable test exercise the main flow end to end, reusing the design's worked examples? [L6, L49]
- Is each rule direction and edge case (draw, boundary `t == cutoff`, empty undo) covered? [L7, L9, L29, L81]
- Are illegal inputs rejected before any state changes, and tested? [L93]
- Is time injected, never read from the system clock in logic or tests? [L33, L35, L64]
- Do tests avoid depending on a swappable algorithm's choices, stubbing volatile collaborators? [L10]
- Were characterization tests run before and after the refactor? [L16, L32]
- Do concurrency tests run many interleavings and assert on returned values? [L55, L62, L84]
