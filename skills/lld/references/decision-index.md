# LLD decision index

Use this when you need a fast call mid-task. Find your situation's group, match the **When** signal, take the **Do**. "Flips" names the condition that reverses it. The link after each group goes deeper. `(inf)` = generalisation not stated in the course.

**Groups:** [Scoping](#scoping) · [Boundaries](#boundaries) · [Inheritance](#inheritance) · [Extending code](#extending) · [Creation](#creation) · [Algorithms](#algorithms) · [State](#state) · [Async](#async) · [Ordering](#ordering) · [Caching](#caching) · [Messaging](#messaging) · [Resilience](#resilience) · [Persistence](#persistence) · [APIs](#apis) · [Testing](#testing) · [Interview](#interview) · [Disagreements](#disagreements)

## Scoping
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Open "design X" prompt | Numbered feature list; mark the few you build | Explicit scope. Flips: list given | [L42, L93] |
| Ranking features | Pick the core algorithm/state; park auth, notifications, billing | Hard part is graded. Flips: parked item is the focus | [L42, L50, L86] |
| Infra component (queue, limiter) | Derive classes from the API list | Few actors. Flips: consumer product, start from flows | [L90] |
| Data-holding component | Walk CRUD, attach a policy to each op | Surfaces immutability, replay, ordering | [L51, L61] |
| Stateful component | Name the consistency guarantee before coding | It drives what blocks | [L52] |
| Writing models | Write the using behaviour first, add only needed state | Models-first guesses fields | [L50, L47] |
| Judging a design or PR | Score readability, extensibility, correctness; ask what the next feature costs | Shared vocabulary; correctness non-negotiable | [L1, L2] |
| "Objectively detect X" | Implement exactly the bounded check | Deeper search = smarter but worse code | [L17] |
| Many cleanups possible | Order by payoff / effort | Flips: one blocks correctness | [L23] |

See [workflow.md](workflow.md).

## Boundaries
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Placing a method | Ask who you would go to if it changed | Practical "one reason to change" | [L8] |
| Rule-of-the-world question (legal, over, winner) | Rules class, not engine or AI | Rules are facts; strategy consumes them | [L8, L17] |
| Heuristics or choice | Own class (AIEngine, Strategy) | Changes independently | [L8] |
| Name is Manager/Main, or lies about its type | Rename to what it decides or holds (`RuleEngine`, `Amount`) | Hidden responsibility, misuse | [L4, L8, L12, L47] |
| Coordinator calls another object's setters, or callers chain `a.getB().add()` | Intent-level method on the owner; private fields | Owner validates and can swap structure | [L8, L41, L82, L90] |
| Mutated collection field, or nested generics | Named class (`ActiveOrders`, `RuleSet`, `BalanceMap`) | A type is missing; storage leaks | [L23, L47, L87] |
| Several maps share a key | One `id -> Object` map | No sync burden | [L90, L66] |
| Bare String/long IDs | Wrapper types | Compiler catches swaps. Flips: throwaway script | [L68] |
| Identity plus per-session attributes | Split `User` / `Player` | Session data changes, id does not | [L22, L89] |
| Per-entity state on parent (fields, parallel arrays) | Move it onto the entity, or one keyed map | Scales to N, cannot drift | [L22, L43] |
| Unbounded collection that doesn't define the object | Association object; parent id on child | No bloat; fast reverse lookup | [L43] |
| Literals or >2 closed values | Scoped enum / named constant; boolean only if truly binary | Survives change | [L31, L87] |

See [principles-and-smells.md](principles-and-smells.md).

## Inheritance
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| About to write `extends` | Say "X is a Y"; reject if false | Timed game *has* a config | [L21, L82] |
| Variation is configuration | Compose a `Config`; delegate on it | Flips: subtypes differ in behaviour and substitute | [L21, L22] |
| Subclass throws or ignores inherited behaviour | LSP violation; compose | Child must honour parent | [L21, L40] |
| Base builder must return different subtypes, or you need a downcast | Compose shared `Details` into each type | Casts move errors to runtime | [L40, L41] |
| Method fits many but not all implementations | Sub-interface (`CellBoard`) | Root stays universal. Flips: every plausible type has it | [L27, L23] |
| Unsure a member belongs on the base | Keep it on the subtype | Hoisting later is cheap. Flips: spec stable for years | [L5] |
| All methods abstract | Interface | No shared state | [L13, L87] |
| Shared fields or steps inside operations | Abstract class (template method) | One home; spends the inheritance slot | [L82, L89] |
| `type ==` / `instanceof` switch in base | Subclass override | Tolerable only while one variant exists | [L82, L5] |
| Typing a collaborator | Narrowest abstraction providing the called methods | Reuse. Flips: logic is truly one type, so say so | [L28, L26] |
| Introducing a hierarchy | Check LSP, ISP, DIP then; SRP and OCP always | Makes the hierarchy hold | [L28] |
| Event subclasses add only a label | One `Event` with a `type` field | Keep subclasses if fields differ | [L41] |

See [principles-and-smells.md](principles-and-smells.md), [patterns.md](patterns.md).

## Extending
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Feature = another branch in a method | Varying logic into objects (rule list) passed to the core | Core stays closed | [L18, L20, L91] |
| Checks independent, order-free | Rule list or set, keyed by type | Flips: one or two stable checks | [L18] |
| Ordered "try A, else B" | Chain of Responsibility or named if/else helpers | A set loses order. Flips: runtime-configurable order, build one ordered list | [L22, L24, L26] |
| Input or config picks algorithm | Strategy | Strategies are isolated | [L32, L78, L87] |
| Better algorithm, same job | One public method; select inside | Flips: user picks mode, pass a parameter | [L11] |
| Branches look like phases | State only with a sparse, finite transition graph | Reject if `nextState` needs the global if/else | [L32] |
| New field doesn't fit a type's meaning | New type or extracted logic; no wrapper onion | Inner changes ripple out | [L17, L19, L20] |
| Extending tested code | Add beside it | Tested code is known-correct | [L11] |
| Cross-cutting service with growing inputs | `execute(Command)` built by a builder; rules in the builder | Flips: one call site, stable args | [L39] |
| Copying a class for a new channel | Extract shared state first | Copies rot | [L40] |
| Policy may vary per caller | Strategy plus default on null; ship one impl | Cheap extension point | [L78, L64] |
| Pattern attempt leaves the smell | Throw it away | The smell is the test | [L32, L23] |

See [patterns.md](patterns.md).

## Creation
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Overloads multiply; callers pass placeholder nulls | Builder with defaults | Flips: few required fields; one-param builder, use a constructor | [L19, L41] |
| Implicit start state, derived fields, "may this exist?" checks | Factory, one named method per use case | Builder = many fields; factory = init logic | [L34, L35] |
| Long repeated test setup | Fix creation in production (factory) | Real call sites share the pain | [L34] |
| Stateless handler re-instantiated | Single instance via DI | Hand-rolled has thread traps. Flips: interviewer wants it written | [L25, L26] |
| Immutable values created repeatedly | Flyweight via static accessor, array-indexed | Flips: object cheaper than the lookup | [L35] |
| Contended expensive resource | Bounded object pool | Not a bare semaphore | [L94] |
| Expensive object maybe unused | Lazy Proxy | Flips: strict memory ceiling | [L30] |

See [patterns.md](patterns.md).

## Algorithms
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Lookup by id and by min/oldest | HashMap plus TreeMap/heap with the right comparator | No single structure does both. Flips: tiny n | [L83, L57] |
| Mutated field is not the sort key | Mutate via map, skip re-index | Flips: sort key changes, remove and re-insert | [L83] |
| Exact-key lookup | Concurrent hash map | O(1) | [L70] |
| "After T" or range | Sorted map (skip list) seek, then scan | Hash can't answer nearest | [L67, L70] |
| Append-only time-ordered list | Binary search the start | O(log N) | [L89] |
| Settle zero-sum balances | Two max-heaps, pair largest with largest | <= n-1 edges; heuristic, not optimal | [L44, L48] |
| Service dependencies | Topological sort | Order respects deps | [L85] |
| Infinite data (recurrence) | Store a generator, expand on read, jump to window | Materialising infeasible | [L86] |
| Check after an incremental change | Check only what changed; running aggregates for O(1) | Costs an invariant on every mutation | [L93] |
| Loop duplicated except traversal | Pass a function (2-D) or iterator (1-D) | Flips: shapes will diverge, merge goes rigid | [L14, L15, L16] |
| 3-5 nested loops | Ask: graph search, bounded search, existing operation? | Per-level helpers are cosmetic | [L17, L31] |

See [case-studies/README.md](case-studies/README.md).

## State
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Hypothetical moves or what-if | Run on a copy (Prototype) | Flips: single-threaded, trivial undo, allocation-bound | [L12, L13, L82] |
| Undo needed | Invert if trivial; replay or snapshot if it cascades | Inverse of cascades is error-prone | [L29, L93] |
| Writing `copy()` | Share only immutable or always-replaced refs | Shared mutable ref corrupts original | [L13] |
| Method returns a modified copy | Always assign the result | Dropped return is a silent no-op | [L37] |
| Multi-field invariant, concurrent readers | Build new immutable object, swap reference | Flips: no staleness allowed, use a RW lock | [L45] |
| Stale vs inconsistent | Stale | Half-updated data is meaningless | [L45] |
| Terminal state | Guard all mutators; result logic stays in the owner | Post-terminal moves corrupt state | [L36, L37] |
| Several mechanisms set one outcome | Explicit precedence; one combined predicate, one side effect | Avoids double-apply | [L37] |
| Invariant on an entity | Enforce in setter or add; throw with context | Bad callers pass silently | [L13, L43] |
| Derivable flag | Derive it | Fewer disagreeing fields | [L82] |
| "Not set" or "no result" | Sentinel, `Optional`, or default object | Nulls caused live bugs | [L16, L25, L83] |
| Settle, correct, delete records | Flag or compensating record; no overwrite | History is the product | [L43, L61, L90] |
| Status over time | Enum on entity plus append-only log | One source of truth | [L94] |

See [principles-and-smells.md](principles-and-smells.md).

## Async
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Request thread would hit slow I/O | Return a Future; work off-thread | Bounded pool drains. Flips: in-process and fast | [L54, L75] |
| Remote-backed method | `CompletableFuture<T>` (`<Void>` for writes) | Signature announces I/O and failure | [L56, L79] |
| Local decision | Plain return value | A future falsely signals I/O | [L73, L80] |
| Chaining after async | Compose with `...Async(fn, executor)`; no `get()` or `join()` inside | Blocking holds the thread hostage | [L56, L59, L79] |
| Building an async result | Value and exception paths; timeout on waits | Otherwise callers wait forever | [L54, L84] |
| Constructor needs remote data | Inject the resolved object | Construction can't fail on the network | [L79] |
| Library inside a host process | Own small pool for own I/O; caller owns callback threads | Isolation | [L77, L80] |
| Placing pools | At gateway and DAO edges, not controllers; sized by config | Controllers stay business-only | [L65, L76] |
| Read waits on another call's data | Register a future the producer completes | No busy-wait | [L84] |
| Holding a lock, waiting on a future that needs it | Release first (inf) | Producer stalls until timeout | [L84] |

See [concurrency-and-async.md](concurrency-and-async.md).

## Ordering
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Per-key order, cross-key parallelism | `executors[hash(key) % N]`, single-threaded each | FIFO, no locks. Flips: no ordering needed, or hot key | [L55, L58, L63, L65] |
| Choosing the routing key | Smallest tuple the guarantee needs | Finer = more concurrency; too fine weakens guarantee | [L62, L68] |
| Any-free-thread pool | Don't assume FIFO completion | Same-key tasks race | [L55] |
| Using locks instead | Set dead-holder policy (TTL or `finally`) | Dead holder blocks all | [L55] |
| State spans two structures | One lock for update and delete | Pair is unsafe even if each is safe | [L84] |
| One write touches several indexes | Single private add and symmetric remove | Side doors leave indexes stale | [L58, L68] |
| Multi-machine events | Don't order by producer timestamps | Clock skew | [L61] |
| Out-of-order halves (end before start) | Buffer, or state a client contract | Else NPEs, leaks | [L84] |
| Documenting | State exact guarantees (per topic, per subscriber-topic) | Callers need the interleavings | [L62] |

See [concurrency-and-async.md](concurrency-and-async.md).

## Caching
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| What to cache | Costly, widely-read data (group-scoped) | Little gain on per-user, rarely re-read data | [L45] |
| Write policy | Write-through: persist, then put on success | Flips: DB write load dominates and loss tolerable, write-back | [L51, L56] |
| Client writes then reads | Read-your-writes: hold that key's ops until ack, block per key | Stronger needs DB invalidation fan-out | [L51, L52] |
| TTL | Key on load time | Hot values still go stale | [L57] |
| TTL plus LRU/LFU | Two sorted indexes; policy only in comparator; LFU ties by LRU | One comparator = one order | [L57, L58] |
| Cache full | Drop expired first, then evict one live key | Live eviction is last resort | [L58] |
| Not full | Lazy expiry, checked on read | No correctness cost | [L58] |
| Concurrent misses, one key | Future placeholder shared by all callers | One I/O serves N | [L59] |
| Hot-loading | Through the normal add path | Side door desyncs indexes | [L59] |
| Cached entity references others | Store IDs; immutable values | Lean; expired, never corrupt | [L45, L47] |

See [concurrency-and-async.md](concurrency-and-async.md).

## Messaging
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Action triggers others' follow-ups | Publish to a bus | New consumer = one line. Flips: one fixed consumer, result needed now | [L41, L60] |
| Observer proposed | Only for runtime-varying subscriber types | Single fixed recipient or self-listening: no | [L87, L94] |
| Event shape | Id, type, self-sufficient payload; immutable | Dedupe, quick filter | [L60, L61] |
| Consumers want subsets | Topics plus bus-side predicate | No wasted traffic | [L66, L90] |
| Publisher retries | Idempotent on event id | No duplicate effects | [L61] |
| Push fails | Retry retryable errors with `base*2^(n-1)`, then DLQ | Evidence without blocking | [L64, L68, L90] |
| Pull consumer resumes | Bus-held per-(topic, subscriber) cursor; no delete on read | Clients don't persist cursors | [L67, L90] |
| Handler mixed with poll/sleep | Split "when" (bus) from "what" (handler) | Testable alone | [L41] |
| Push consumer lags | Per-subscriber back pressure | Pull self-paces | [L90] |
| Many clients, rare changes | Push: SSE one-way, WebSocket two-way; long poll as fallback | Polling costly at scale | [L87, L88] |
| Skewed follower counts | Push normal, pull celebrities on read | Celebrity push overloads | [L89] |

See [patterns.md](patterns.md), [case-studies/README.md](case-studies/README.md).

## Resilience
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Load can exceed capacity | Edge accept/reject limiter only | Degradation is a different tool | [L71] |
| Limit check on hot path | In-process client decides; server stores config | Flips: exact global enforcement needed | [L72, L74, L81] |
| Limit spans N instances | Sync aggregates on an interval | Local limits sum too high | [L72, L74] |
| Limiter unreachable | Fail open | Not a SPOF. Flips: overrun worse than outage | [L72, L74] |
| Keying limits | Opaque key; composite for exotic rules | Covers custom rules | [L74] |
| Sliding window | Store timestamps; evict head before compare | Stale entries cause false rejects | [L78, L81] |
| Downstream fails below capacity | Cut threshold on reject; grow fractionally, never +1 | +1 never rejects | [L80] |
| Rejection | Retryable error; caller-owned callbacks | Same request may pass later | [L71, L77] |
| Money order fails | Fail and notify, no auto-retry | Price moved | [L87] |

See [concurrency-and-async.md](concurrency-and-async.md).

## Persistence
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Product schema | Features, APIs, objects, tables; layout from your SQL | Flips: tuning an existing schema | [L92] |
| List column or two-sided many-to-many | Indexed join table holding relation attributes | Flips: one access direction | [L86, L92] |
| Normal form | 2NF-3NF; denormalise a parent id for hot reverse reads | Controlled redundancy is normal | [L43, L92] |
| Per-object permissions | `(subject, relation, object)` rows; flat before Zanzibar | Change often, survive restarts | [L92] |
| Versioned content | Content-hash blobs, immutable trees, path copying | Dedupe, shared structure | [L92] |
| Finding rules to evaluate | Indexed metadata columns, then run the engine | JSON search is slow | [L91] |
| Persisting rules | Serialise to JSON/DSL, parse back; admin UI over config files | Flips: bespoke rules, keep a few in code | [L18, L91] |
| Per-user usage limits | Usage table per (coupon, user) | A counter can't say who | [L91] |
| Controller needs data | DAO per table, futures, typed rows | One home per table | [L76] |
| Queue acks a write | Ack after DB accepts; rebuild on restart | Ack is the durability promise | [L90] |
| Who makes IDs | Server: no collisions. Client composite: idempotent retries | Attributes don't dedupe | [L86] |

See [data-modeling-and-apis.md](data-modeling-and-apis.md).

## APIs
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| Fuzzy requirement | Write caller signatures first | Nouns become classes | [L3, L56] |
| >2 outcomes or data | Result object, not boolean | Win, draw, in-progress | [L3, L93] |
| May be absent | `Optional`; domain exception if it must exist | Absence in the signature | [L25, L66] |
| Param and return types | Accept general, return specific | No casts downstream | [L31] |
| Param only echoed back | Drop it, return less | Caller has it | [L24] |
| Value rides beside an object | Fold it in (`Move` holds `Player`) | Belongs to the concept | [L8] |
| Constant for a client's life | Constructor arg, stamped per request | Less noise | [L77] |
| Trusted value (price, createdAt) | From server state | Never trust the client | [L87, L89] |
| Variants need different inputs | Send the raw fact; server config decides | Clients unchanged | [L22] |
| Update in disguise (RSVP) | Fold into an existing endpoint | Fewer APIs | [L86] |
| Shared-resource read | Resource id plus caller id; check membership first | Authz before work | [L46, L47] |
| Nothing to return yet | Dedicated response type, id = request id | Add fields later | [L75] |
| Overload picks behaviour | One method, named params | Types shouldn't carry logic | [L33] |
| Internals need richer return | Private helper | Keep public API clean | [L57] |
| Exceptions | Narrow types; distinct "gave up" type | Targeted handling | [L64, L79] |
| Enums and units over the wire | Client enum mirroring server; `Duration` | Unit bugs happened | [L37, L80] |
| Others call your service | Client library, one entry class | Methods, not wire formats | [L77] |

See [data-modeling-and-apis.md](data-modeling-and-apis.md).

## Testing
| When | Do | Because / flips when | Refs |
|---|---|---|---|
| In-process monolith | Plain unit tests; mocks only at external edges | Deterministic, cheap | [L8, L9] |
| Multi-class flow | Name test by behaviour | `<Class>Test` for true units | [L9] |
| Depends on evolving AI or heuristic | Stub it or set state; script both sides | Survives a smarter AI | [L10, L13] |
| Time or sleep in logic | Inject a clock; hand-checkable numbers | Deterministic, fast | [L35, L36, L64] |
| Untested class to change | Test public methods first | Safety net | [L33] |
| Test covers factory and product | Split | Localise failures | [L37] |
| Validation breaks tests | Fix inputs, not logic | No tests tied to outputs | [L13] |
| Unexpected green | Re-derive the expected result by hand | Green can be wrong | [L12, L36] |
| Wrong across layers | Assert bottom-up | Finds the faulty layer | [L49] |
| Graph or set result | Compare unordered | Order irrelevant | [L49] |
| Many bugs at once | Nulls, then interactions, then concurrency | Each masks the next | [L69] |
| Concurrency | Contract-respecting client, thousands of random interleavings | Calls alone miss races | [L84] |

See [testing.md](testing.md).

## Interview
Interview-only tactics.

| When | Do | Because / flips when | Refs |
|---|---|---|---|
| 1-hour round | ~30 min board (requirements, objects, APIs, concurrency), rest codes core plus a test | Thinking live takes time | [L45, L50] |
| Timed coding | Core public method first, top-down | Core survives a time-out | [L47, L48] |
| CRUD, auth, storage | Stub or mock and say so | Nuance is graded | [L45, L46] |
| Heuristic algorithm | Say so; keep a counterexample; name the exact method | It will be probed | [L44] |
| 45-60 min LLD | Name threading, packages, risks; don't build them | Build in long rounds | [L53, L75, L85] |
| Peripheral rules (castling) | Stub and confirm out of scope | Decomposition graded | [L82] |
| Time nearly up | Happy-path tests on the core | Enough to close | [L49] |
| Any choice | Say the trade-off aloud | Explanation is graded | [L86] |

See [workflow.md](workflow.md), [case-studies/README.md](case-studies/README.md).

## Disagreements
- **Class inheritance:** L46 calls it rare, while L75, L82 and L89 use abstract bases. **Final:** use an abstract class when "is-a" holds and there are shared fields or steps; otherwise interface plus composition.
- **Rule list vs if/else:** L18 uses a list; L22 and L24 reject it for ordered logic. **Final:** list only when rules are order-free.
- **Undo:** L12-13 copy with replay, L29 snapshots, L93 inverts. **Final:** invert when trivial, replay or snapshot when it cascades, copy for exploration.
- **DRY traversal:** L14 BiFunction, L15 iterator, L16 reverts the over-merge. **Final:** function for 2-D, iterator for 1-D; stop when readability drops.
