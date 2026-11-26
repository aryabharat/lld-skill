# Design principles, code smells and the refactoring method

Use this when deciding where a method or field belongs, whether to add an abstraction, reviewing a PR for design problems, or planning a refactor. Part 1 gives each principle as a decision rule plus the point where it stops applying. Part 2 is a smell lookup table. Part 3 is the order of work for a refactor.

**Contents:** Part 1 Principles (SRP, OCP, LSP, ISP, DIP, DRY, encapsulation, composition vs inheritance, naming, immutability, nested structures, restraint) | Part 2 Smell catalogue | Part 3 Refactoring method | Interview-only notes

How the course groups SOLID: SRP and OCP are ongoing goals for every class. LSP, ISP and DIP are checks you run the moment you write `extends` or `implements`. [L28]

---

## Part 1: Principles as decision rules

### 1. Single Responsibility (SRP)

- **When** unsure which class gets a method -> **Do** ask "if this behaviour had to change, which class would I open?" -> **Because** that is the working meaning of "one reason to change". [L8, L10]
- Course example: the tic-tac-toe god class became `GameEngine` (runs moves), `RuleEngine` (fixed truths: legal? over? who won?) and `AIEngine` (choices under uncertainty). The AI uses the rule engine but never owns rules or mutates the board. [L8, L10, L11, L17]
- **When** a coordinator calls another object's low-level mutators (`board.setCell`) -> **Do** give the owner one high-level operation (`board.move(move)`). [L8]
- **When** a value is passed beside an object on every call (`move(board, player, move)`) -> **Do** fold it into the object (`Move` holds `Player`). **Flips when** it varies independently. [L8]
- **When** creation needs business checks (profile exists, not already in a game) -> put them in the factory, not the constructor. [L34, L35]
- **When** a getter promises a full answer (`getWinner()`) -> every path that decides it (timeout, winning move) lives in that class. [L37]
- **Stops applying:** packages isolate concerns but are not SRP; SRP alone doesn't make code readable or extensible. [L10]
- **Reviewer:** the feature diff should land in the class named for that concern. A strategy that writes state, or a sender that decides *whether* to send, fails. [L10, L39]

### 2. Open/Closed (OCP)

- **When** every feature PR edits the same `if (check) return state;` chain -> **Do** make each condition a `Rule` and have the function loop over an injected list -> **Because** new behaviour becomes new data and the tested core stops changing. [L17, L18, L20]
- **When** about to extend by wrapping (`GameInfo` around `GameState`, then another wrapper) -> **Do** check whether the behaviour is a separate concern; extract and inject it -> **Because** wrappers stack into an onion whose core nobody dares touch. **Flips when** it is genuine cross-cutting decoration. [L17, L19, L20]
- The engine should know *how* to evaluate rules, not *what* they are. Per-type rule lists use a type-safe key, not a class-name string. [L18, L23]
- **When** a component gains a better algorithm -> keep one public method and select internally, never `doX`/`doSmartX`. **Flips when** the caller really chooses (difficulty): pass a parameter or strategy. [L11]
- Measure "closed" by how rarely the core changes, not by feature count. [L20]
- **Stops applying:** one or two stable checks (inferred) [L18]; order-dependent rules, because a rule *set* loses order (use extracted if/else branches or Chain of Responsibility with explicit `next()`) [L22, L24, L26]; no pending change, so don't apply it speculatively [L14]. Rules in config/DB is the next step up, but encoding logic in config is hard and a code list gives most of the benefit. [L18]

```java
interface Rule<B> { Optional<GameState> evaluate(B board); }
class RuleEngine {
  GameState getState(Board b) {
    for (Rule r : rulesFor(b)) {                 // knows how, not what
      Optional<GameState> s = r.evaluate(b);
      if (s.isPresent()) return s.get();
    }
    return GameState.inProgress();               // default object, not null
  }
}
```

### 3. Liskov Substitution (LSP) and the base-class question

- **When** deciding whether a member goes on the base -> **Do** ask "does every current and plausible future subtype have this, in this exact form?" If no or unsure, keep it on the subtype -> **Because** hoisting later is cheaper than un-hoisting (inferred). **Flips when** the domain is fixed and stable for years. [L5, L23]
- Course example: `getSymbol(i, j)` on `Board` compiles and runs, but chess cells hold pieces and hex/3D boards have no (i, j), so it was rejected. [L23, L27]
- **When** a subclass would ignore, disable or throw from inherited behaviour -> LSP violation; compose instead. [L21, L40]
- **When** consumers demand a specific subtype of the base they were handed -> the hierarchy is wrong. [L40, L41]
- **When** tempted to cast ("I know it's a TicTacToeBoard here") -> carry the type in a generic or narrow interface; a cast has no structural guarantee. [L23, L27]
- **Reviewer:** reject base methods only one implementation can honour and overload families per coordinate system. `instanceof` chains in an engine are a tolerable stopgap only while one subtype exists. [L3, L5, L23]

### 4. Interface Segregation (ISP)

- **When** a method fits many but not all implementations -> **Do** put it on a capability sub-interface (`CellBoard extends Board`) and type consumers against it (`CellRule`) -> **Because** the root stays implementable by every future type and the precondition is compiler-checked. [L27]
- Generics or downcasts that exist only to reach one method signal a missing capability interface; adding `CellBoard` removed every rule's type parameter. [L27]
- Keep only truly universal operations on the root (here: copy, move). [L27]
- **The instructor corrected himself:** withholding shared logic "because a future type might not support it" is over-engineering. Segregate and reuse now. [L27]
- **Production:** split large services along the same capability seams. [L27, L28]

### 5. Dependency Inversion (DIP)

- **When** typing a parameter or field -> **Do** use the narrowest abstraction providing the methods you call (`CellBoard`, not `TicTacToeBoard`, not `Board` if you need cells) -> **Because** every implementation can reuse the code; DIP is how OCP is implemented. [L28]
- Return the most specific type you produce (`DefensivePlacement get()`), so callers avoid casts. [L31]
- **Apparent contradiction:** the AI heuristics only make sense on 3x3, so L26 takes the *concrete* type on purpose; a generic signature would promise what the code cannot do. Final position: the narrowest *honest* type wins. [L26, L28, L31]
- **Production:** injecting clocks, executors and already-resolved config is the same rule. [L35, L64, L79]

### 6. DRY, and the overfitting risk

- **When** two blocks look alike -> **Do** diff them line by line; if the differences reduce to one or two expressions (an index mapping), pass those as a function and keep one body. [L14, L15]
- Iterator suits a single sequence; a two-coordinate walk fits an index-mapping function (`(i, j) -> cell`) better, which is where L15 landed. [L15]
- Same pre-step at every call site (copy, then mutate) -> fold it into the method. Branch arms differing only in inputs -> assign the values under one condition, make one call. [L29, L33]
- **The risk:** deduping by matching tokens instead of a domain concept yields abstractions named after mechanics (`apply(0)`) that overfit today. A zigzag traversal would not fit the merged shape and changes would cascade. [L15, L16]
- After a DRY refactor, fix names first (`getGameState` -> `isVictory`) and drop micro-optimisations that forced extra branches, then decide keep vs revert. Judge on correctness, readability and extensibility, never lines saved: 90 -> 60 lines coincided with worse readability. [L14, L16]
- **Stops applying:** if extraction is genuinely impossible, duplication is the accepted last resort. When dependent checks each perform a side effect, one decision point beats shared helpers. [L37, L41]
- **Reviewer:** ask what the shared abstraction is called in the domain and which input shape would break it. [L16]

### 7. Encapsulation and validate-at-entry

- **When** other code touches a raw field or collection (`obj.cells[i] = x`, `topic.getMessages().add(m)`) -> **Do** make it private and expose intent methods (`topic.addMessage(m)`, `board.setPiece(r, c, p)`) -> **Because** a method is a choke point for validation and lets you swap storage (history moved map -> list with zero outside edits). [L4, L29, L82, L90]
- Read-then-act across a boundary (get offset, fetch, bump) -> one method on the owner (`topic.getNext(sub)`). [L90]
- Invariants (cell set once; expense balances sum to zero) -> check in the mutator or on add/edit; throw `IllegalArgumentException` with context. [L13, L43]
- Terminal state -> guard every mutator. Server-owned fields (`createdAt`, market price) -> set in the service, never from the client. Orchestrators -> validate and fail fast before downstream calls. [L36, L85, L87, L89]
- `a.getB().getC()` -> delegating accessor on `a`. [L41]
- **Where lessons differ:** L89 let the service mutate a returned `getComments()` list and put the 140-char check in a service layer; its analysis says production code should expose add/remove and return unmodifiable views. Final position: invariants live on the owner; request-shape checks may sit in a validation layer; never leak a mutable internal collection. [L89, L90]

### 8. Composition vs inheritance

- **When** about to write `X extends Y` -> **Do** say "X is a Y" aloud; reject if false. A timed game *has* a config. Swapping abstract class for interface doesn't fix a wrong is-a. [L21, L82]
- Variants that differ only by setup (timed, untimed, two moves per turn) -> one class composing `GameConfig`; mode-only subclasses collapse. [L21, L22]
- Orthogonal concern (clocks vs positions) -> keep the core ignorant; a new class uses it (`Game` has a `Board`). Per-participant state goes on the participant (`player.timeUsed`), with stable `User` split from per-game `Player`. [L21, L22]
- **When** a shared builder's `build()` must return different concrete types -> drop inheritance; each command/builder holds a shared `NotificationDetails`. Rejected: downcasting (fails at runtime) and `buildEmail()/buildSms()` on the base (edit per channel). [L40, L41]
- **Inheritance is right when** subtypes differ in behaviour and are substitutable: chess `Piece` is an abstract class (template method for capture and king-in-check). Siblings sharing a collection field get a capability base; abstract class if it holds state, interface if only signatures. [L21, L82, L89]

### 9. Naming that doesn't lie

- Name classes by the decision they own: `RuleEngine`, not `GameManager`; `GameEngine`, not `Main`. [L4, L8]
- Rename when the return type changes: `getCell` returning `String` -> `getSymbol`; `getSmartMove` returning `Cell` -> `getCellToPlay`-style. [L12, L24]
- Neutral names for general concepts (`key`, not `request`, in a limiter); domain names over type names (`TimeUnitEnum`). [L74, L80]
- Return honest types: an aggregation returning a fake "Expense" holding a sum is lying. [L47]
- Full local names (`secondPlayerMoves`, not `sRow`, `cc`). [L13, L93]

### 10. Immutability and value objects

- Money -> `Balance`/`Money` with currency. Correlated fields (hasFork, forkCell, forkPlayer) -> consider a `Fork` value object, but only once it hurts; the instructor deferred it. [L24, L43]
- **When** exploring hypotheticals (AI lookahead, "does this move expose my king?") -> work on a copy (`board.copy()`, `player.flip()`); every reference field in the copy must be immutable. **Flips when** undo is trivial, single-threaded and allocation matters. [L12, L13, L82]
- Copy-returning methods -> always reassign (`board = board.move(m)`); pick one model. [L37]
- **When** a multi-field invariant changes under concurrent readers -> build a new immutable object and swap the reference; stale beats inconsistent. **Flips when** reads must be fresh: read/write lock. [L45]
- Repeated identical immutable values -> share instances (Flyweight), unless lookup costs as much as construction. [L35]
- History-bearing records -> status flag or append-only plus compensating event, never overwrite. Policy fields -> constructor-injected and `final`. [L42, L43, L56, L61]

### 11. Extract nested structures into classes

- **When** a type reads `Map<K, List<Rule<T>>>` -> **Do** wrap it (`RuleSet`) with a private non-null store and intent methods (`add`, `forEach`) -> **Because** nesting hides meaning, swapped arguments compile, and storage choice leaks to callers. [L23, L47, L68]
- Several maps sharing a key -> one map `id -> Aggregate`. Index-coupled lists -> one map keyed by entity. [L43, L66, L90]
- A growing collection that doesn't define its owner (group -> expenses) -> association object keyed by parent id. [L43]
- Every write path (get-miss, set, hot load) goes through one insert method that updates all indexes. [L58, L59, L68]

### 12. Restraint (YAGNI-style)

Don't create: empty packages or classes you can't justify [L4, L21]; a utility class before a second caller [L11]; a `symbol` on shared `Cell` before the requirement [L31]; a builder for one parameter and one way to build [L41]; a hierarchy before behaviours show commonality [L82]; fields no method uses [L50]; more than the bounded check asked for (fork detection is two plies, not a search engine) [L17]; algorithmic refinements before metrics demand them [L80]. **Counterweight:** restraint is not refusing reuse available today (paranoid abstraction). [L27]

---

## Part 2: Smell catalogue

| Smell | How to spot it in code | Fix | Refs |
|---|---|---|---|
| God class / method | One class builds, mutates, judges, strategises; ~90-line method | Split by reason to change | L8, L14 |
| Hot-fix accretion | Each bug fix adds a nested check or flag to one function | Restructure; extract per-case checks | L7 |
| Growing if-chain | Every feature edits the same `if ... return` sequence | Rule list + engine, or strategies | L17, L18, L24 |
| Onion of wrappers | `getInfo` wraps `getState`; outer class takes inner whole | Extract and inject; take only used fields | L17, L19, L20 |
| Type dispatch | `instanceof` chain in engine; `if (type == PAWN)` in parent | Override or per-type strategy | L3, L5, L82 |
| Fat base interface | Root methods some types can't honour; per-coordinate overloads | Capability sub-interface | L23, L27 |
| Downcast in business code | `(EmailCommand) builder.build()` | Generics, narrow interface, composition | L23, L40, L41 |
| Per-subtype methods on base | `buildEmail()`, `buildSms()`, `event.toEmail()` | Move to the variant | L40, L41 |
| Mode-only subclass / concept pollution | `TimedGame` vs `LeisureGame`; time on Board | Field or composed config | L21, L31 |
| Indexed per-participant state | `player1X`, `xs[i]`, lockstep lists | State on participant; map by entity | L22, L43 |
| Copy-paste siblings | Blocks differing only in index; mirror-image methods | Parameterise the difference | L14, L15, L93 |
| Token-driven DRY | Abstraction named after mechanics; nameless lambdas | Name the domain concept or keep duplication | L16 |
| Flag plumbing | Synonym flags; set-break-check; optimistic `true` default | Return at discovery; derive from guard | L7, L14, L31 |
| Leaky micro-optimisation | Special-cased first element, extra supplier to save one compare | Delete it | L14, L15 |
| Deep nesting | 3-5 levels of loops/ifs | Reuse domain ops, early return; is it a traversal? | L17, L22, L31 |
| Null as "no result" | `if (x != null)` everywhere, some impossible | Default object or `Optional` | L16, L25 |
| Misleading or cryptic names | `getCell` returns String; `Manager`; `sRow` | Rename to what it returns/decides | L8, L12, L13 |
| Magic values | `count < 2`, `new Cell(1,1)`, `"X"` | Named predicate/constant; nested enum | L11, L24, L31 |
| Leaked internals | Public fields, `getMessages().add()`, `a.getB().getC()`, split read-then-act | Private + intent/delegating methods | L4, L41, L90 |
| Unenforced invariant / no terminal guard | Setter accepts anything; moves after game over | Validate in mutator; guard mutators | L13, L36, L43 |
| Mutating during a query | "Check" loop calls a mutator, never reverts | Evaluate on a copy | L12 |
| Aliased copy / dropped copy | Copy shares a mutable member; `board.move(x);` bare | Deep copy or immutable; reassign | L13, L37 |
| Nested generics / parallel maps | `Map<K, List<X<Y>>>`; `.get().get().put()` | Named wrapper; one aggregate per id | L23, L68, L90 |
| Write-path bypass | One code path writes a structure directly; indexes drift | Single insert method | L58, L59, L68 |
| Constructor explosion | Overloads double per optional field; callers pass `null, 0, false`; derivable flags passed in | Builder (optional fields) or factory (defaults, derivation) | L19, L34, L35 |
| Redundant param / state | Param only echoed in return; boolean implied by position | Drop or derive | L15, L24, L82 |
| Parameter sprawl on shared service | Method keeps gaining optional args | Command object + builder | L39 |
| Logic in wrong layer | Email rules in game code; "should I send" in sender | Move to command builder | L39 |
| Hidden ordering | Rule order visible only in registration code | Explicit `next()` or if/else | L22, L26 |
| Fake state machine | States recomputed from globals; same transition block in each state | Classification + strategy | L32 |
| Pattern-first refactor | Pattern picked first; key method won't write cleanly | Stop; choose another structure | L32, L87 |
| Bare money / destructive history | `int amount`; settle overwrites record | Money VO; status flag, append-only | L42, L43, L61 |
| Speculative design | Empty package, unjustified class, unread fields | Delete or condense | L4, L21, L50 |
| Paranoid abstraction / fake generality | Reuse withheld for hypothetical types; abstract param that works for one subtype | Capability interface; honest narrow type | L26, L27 |
| Wall clock in logic | Inline `currentTimeMillis()`; clock read twice per op | Inject clock; capture `now` once | L35, L57, L83 |
| Algorithm-coupled tests | Scripted moves against a live AI; wins only a weak opponent allows | Stub collaborator; test rules on fixed state | L10, L13 |
| False greens | Suite green after a real change; first-run pass | Re-derive expectations by hand | L12, L36 |
| Two units, one test | Factory bug surfaces in game-logic test | Separate factory test | L37 |
| Lines-of-code metric | PR justified by shrinkage | Judge tests, readability, extensibility | L16 |

---

## Part 3: Refactoring method

1. **Make it work first.** Run the draft end to end; refactoring broken code gives the customer nothing. On an unexpected result, debug against expected state before touching design. [L6, L7, L37]
2. **List where it can improve before deciding how** (duplication, coupling, layout, naming). Start from real pain, not a principle or pattern name. [L4, L14]
3. **Prioritise by payoff / effort** and work in that order; don't do every cleanup. Correctness blockers jump the queue (inferred). Start with the dirtiest code. [L23, L31, L82]
4. **Tests first.** A class with no callers gets a test that builds it and calls its public methods. Test the contract, not private helpers. Pin current behaviour before changing for a new requirement. Long repeated test setup signals production creation is too complex: fix it with a factory in production code. [L33, L34, L82]
5. **One change at a time.** Write and run one test before the next. One refactor, run the suite, review the IDE's diff by hand (it wired the wrong variable in L33). [L9, L14, L33]
6. **Treat surprises as information.** A real change with an all-green suite means the tests miss it. Validation that breaks many tests means they used illegal inputs: fix inputs, don't loosen logic or rewrite assertions to match. [L12, L13]
7. **Try it and look.** When unsure, make the change locally, run tests, discard if worse; the instructor prefers this to pure up-front reasoning. [L16]
8. **Revert what cost more than it gained.** L23 rolled back the generics removal but kept the `RuleSet` extraction. L32 abandoned State after one class because `nextState()` needed the same global if/else; the only test of a refactor is whether the original smell is gone. L14 kept a hard-to-read DRY version only after renaming restored readability. Neither auto-keep nor auto-revert. [L14, L23, L32]
9. **Stop when the next step isn't clear.** Name the remaining smell and candidate fixes, then move on to the next ugliest code. [L31]

**Reviewer checklist:** tests existed before the change; each commit does one thing; the original smell is gone; no new casts, nulls or base-type methods; abstractions have domain names; line count is not the justification. [L16, L23, L32, L33]

---

## Interview-only notes

- Graders look at clear objects and names first; keep code formatted. [L46, L83, L93]
- Whiteboard entities and behaviours, sort behaviours into "common to all" vs "special to one", then pick the hierarchy. [L82]
- Hand-written singletons are fine when asked; say production would use DI scopes. [L25, L26]
- If you refactor live, narrate the payoff/effort call and say when you revert. [L23]
