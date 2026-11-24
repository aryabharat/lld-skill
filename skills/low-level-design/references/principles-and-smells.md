# Principles and code smells (with the course's concrete examples)

## Three metrics
- **Readability**: unreadable code becomes a black box, first to be refactored, slows reviews, costs every change.
- **Extensibility**: add features with little modification; code outlives teams.
- **Correctness**: bugs in production are the costliest; reliability is the engineer's core duty. Correctness first - extensibility without correctness is meaningless.

## SOLID
### S - Single Responsibility
- One class/function does one thing well (Unix philosophy).
- Game example: GameEngine (start, move), RuleEngine (legal moves, is it over, winner - "universal truths"), AIEngine (suggest moves only, never mutates). Move carries its Player; Player.flip() lives on Player.
- Payoff: fewer ways data can change, isolation of concerns, one validated entry point per object.
- Packages aren't SRP but support isolation.

### O - Open/Closed
- Open for extension, closed for modification. Wrapping well-tested code is cheaper than changing its heart - but endless wrappers form an "onion" whose core nobody dares touch.
- Real OCP = **extract logic that varies out of the class and pass it in** (rule lists, strategies, chains, observers, builder fields). DIP is how you implement OCP.
- Example: 90-line getState with if-blocks -> list of Rule objects iterated by a pure evaluator; new rule = new object, evaluator unchanged; rules become configuration.
- Don't add `suggestSmartMove` next to `suggestMove`: callers shouldn't choose algorithms - one API, choice inside.

### L - Liskov Substitution
- Subtypes must support all behaviour of the parent. Don't add a base-class method because one implementation needs it (Board.getSymbol(i,j) breaks for chess pieces, hex boards, 3-D boards).
- Builder-base-class trap: base NotificationBuilder.build() returns base type but services need SMSCommand/EmailCommand -> casting or `buildEmail()` methods; fix with composition.

### I - Interface Segregation
- Split interfaces by capability: `Board {move, copy}` for all boards; `CellBoard extends Board {getSymbol(i,j)}` for grid boards. Rules then accept CellBoard; generics disappear. Same idea splits big microservices.

### D - Dependency Inversion
- Depend on abstractions (CellBoard, interfaces), not concrete classes. Inject dependencies (ServiceConfig into the rate-limiter client constructor rather than blocking on a fetch inside it; Timer injected for tests; DataSource into Cache).
- L, I, D are three small rules that make inheritance make sense; S and O are goals you strive for continuously.

## DRY - with a warning
- Put near-duplicate blocks side by side, list exactly what differs, give shared variables one neutral name, pass the difference in as a parameter/lambda/object.
- Over-DRY overfits: shorter but rigid and less readable (a zigzag traversal would break it). Lines of code is not the metric. Good naming partly rescues it; sometimes revert.

## Composition over inheritance
- Inheritance encodes state implicitly in the type; composition stores state explicitly and derives behaviour. Prefer composition when behaviour varies by configuration (TimedGame/LeisureGame -> Game has GameConfig).
- Use inheritance for real is-a with shared behaviour (Rook is a Piece; UpdateRequest is a Request) and prefer inheriting from interfaces in LLD interviews.
- "If you're creating a class without knowing why, delete it or condense via composition."
- Abstract class vs interface: abstract when sharing data members/method bodies (Reactable/Commentable with lists and getters; every car's startEngine); interface for pure contracts, multiple implementation, versioning. Java: single class inheritance, multiple interfaces.

## Encapsulation & APIs
- APIs are the only way to touch your data; wrap raw structures (cells array behind getCell/setCell) so you can validate.
- Private fields + methods on composite objects (Topic.addMessage) so internals can change (list -> set -> map) without callers noticing.
- Hide nested access: `command.getReceiver()` not `command.getDetails().getReceiver()`.
- Return the most specific type; accept the most general type.
- Don't take parameters you don't need; don't take a parameter only to echo it back.
- Keep IO-returning signatures as futures even internally - they signal remote calls.

## Smells and their fixes
| Smell | Fix taught |
|---|---|
| Long method (90 lines) | DRY + extract rules/handlers; prioritise by payoff/effort |
| `instanceof` / `type` switch in a base class | polymorphism (abstract method per subtype), or board supplies its own rules |
| Boolean that needs more info (isComplete) | result object (GameState: over + winner) |
| Magic numbers (2, (1,1) centre) | named constants/thresholds computed from size |
| Nested generics/maps `Map<String, List<Rule<T>>>`, `Map<User, Map<User, Amount>>` | named class (RuleSet, BalanceMap, PaymentGraph) |
| Several maps keyed by the same thing | one map to a composite object (Topic {offsets, pushSubscribers, messages}) |
| Telescoping constructors / many optional params | Builder |
| Complex construction logic repeated | Factory |
| 4-5 nested loops | missing abstraction (reuse placements), graph traversal, flatten; extract methods for readability |
| Nested if/else on game state that changes often | Strategy/Chain if transitions are sparse/ordered; keep if/else + extracted methods if a rule engine would need ordering |
| Overloaded methods whose args mean different things | compute inputs (currentTime, endTime) from config, one comparison |
| Ternaries with long conditions | if-block setting final locals |
| `null` returns spreading | Optional / null object / default value object |
| Redundant state (pawn "hasMoved") | derive from existing state (on start rank) |
| Hard-coded "X"/"O" | enum |
| Mutating shared state while exploring (AI look-ahead) | copy (prototype) or undo |
| Tests coupled to an algorithm | remove the algorithm from the unit; script all inputs |
| Tests using the system clock | inject time/timer |
| Builder that takes one object and builds | delete builder, use constructor |
| Duplicate methods differing only by param type | abstract the param type (Commentable) |
| Hand-rolled polling loops inside a consumer | separate *when* to consume from *what to do* (bus/executor decides) |
| Random micro-optimisations | remove if they add complexity (skip-first-char trick) |

## Refactoring method
- Find problems, then principles (not the other way round). Change code locally to understand it even if you don't commit.
- Priority = payoff / effort; don't fix everything.
- After each refactor run tests; revert when cost > benefit.
- Signal of a good refactor: callers get simpler.
- Clean packages: one class per file; api/game/boards; models/requests/responses/controllers/dao/db/gateway; exceptions/retry/utils.
