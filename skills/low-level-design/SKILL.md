---
name: low-level-design
description: Low-level design (LLD) and machine-coding expert distilled from Gaurav Sen's InterviewReady LLD course (game engine with SOLID + design patterns; machine coding Splitwise, cache, event bus, rate limiter; live classes on chess, Google logger, calendar, Zerodha, Twitter, message queue, coupon engine, Git/DB schema, Zomato). Use when the user asks to design classes/objects/APIs for a system, do an LLD or machine-coding interview problem (e.g. "LLD of parking lot / Splitwise / cache / rate limiter / BookMyShow"), pick a design pattern for a problem, refactor code toward SOLID, review a design or class diagram, design a DB schema for a product, or handle concurrency/ordering/async in a component. Not for distributed-systems HLD (service topology, sharding, capacity) except where it touches a component's internals.
---

# Low-Level Design (from the InterviewReady LLD course)

LLD = turning requirements into well-structured code: objects, their state and behaviour, APIs, interactions, algorithms, concurrency and tests. The yardstick the course uses throughout: **would this code survive a pull-request review?** Judge every design by three metrics: **readability, extensibility, correctness** ("programming is coding across time").

The course's core belief: principles and patterns are *tools that pop out of fixing real problems*, not things to apply up front. Find the smell, name the pain, then reach for the principle/pattern - and be willing to reject a pattern that doesn't fit (the course rejects State, Iterator and Builder in places and reverts a refactor that cost more than it gained).

## How to work

1. **Classify the problem** (decides the flow):
   - *Consumer product* (Splitwise, Twitter, Zerodha, Zomato, Calendar, BookMyShow): use-case diagram -> entities -> services -> class diagram -> sequence/flow -> key method code.
   - *Engineering product* (cache, event bus, message queue, rate limiter, logger, orchestrator, load balancer): skip use-case diagrams; **start from the API**, derive classes, then data structures, concurrency, then tests.
   - *Game/simulation* (chess, tic-tac-toe, snake & ladder): start from the most important class (Board), separate common vs special behaviour, inheritance vs composition decision on the whiteboard.
   - *Schema question*: product-first -> objects -> tables; "what you store comes from requirements, how you store it comes from access patterns".
   - *Refactor/review existing code*: find smells (see `references/principles-and-smells.md`), prioritise by payoff/effort, fix one at a time with tests.
2. Follow the interview/workflow process in `references/process.md` (clarify -> list all requirements -> shortlist core 3-5 -> objects -> APIs -> algorithm -> concurrency -> tests -> extensions).
3. Pick patterns with `references/patterns.md` - every pattern there has the course's "use when / don't use when" and the concrete example it came from.
4. For concurrency, async, ordering, caching, retries, back pressure: `references/concurrency-and-async.md`.
5. For a known problem, reuse the worked solution in `references/case-studies.md` (Splitwise, cache, event bus, rate limiter, Google logger, chess, tic-tac-toe, calendar, Twitter, Zerodha, message queue, coupon engine, orchestration, live scores, Zomato, GitHub schema).
6. Before presenting, run `references/review-checklist.md`.
7. If a local `course-notes/` folder exists next to this file (lesson-by-lesson notes; not distributed in this repo), read the relevant file when you need the exact reasoning or a nuance.

## Non-negotiable habits (repeated across the course)

- **Clarify before designing; draw before coding.** Write requirements, objects and behaviours down neatly - you're explaining to someone else.
- **Shortlist.** List everything, then agree on 3-6 core features. Name what you're deliberately skipping (auth, payments, notifications, CRUD).
- **Attack the main problem first** - work backwards from the critical API's return type; it tells you which models and methods you actually need. Don't start with User/auth plumbing or model boilerplate.
- **Objects first, well named.** Names must not lie (`getCell` that returns a String became `getSymbol`; `Balance` that holds a raw amount became `Amount`). Object definition is the biggest chunk of an LLD interview.
- **Compose small objects; extract anything complex** (nested maps, parallel maps sharing a key, lists that get mutated) into a named class with private state and methods.
- **Interfaces for contracts, composition over inheritance**; inherit only for true is-a with shared behaviour; respect LSP/ISP.
- **Encapsulate and validate at the entry point** - each object owns its data, exposes a small API, validates there.
- **Correctness first, then extensibility.** Write tests; make them deterministic (inject time, inject dependencies); test one unit at a time; don't couple tests to an algorithm that will change.
- **State trade-offs explicitly** (undo vs copy, push vs pull, write-through vs write-back, greedy vs optimal, locks vs ordering). The interview is about seeing trade-offs.
- **Don't over-engineer.** Generic keys and pluggable strategies beat elaborate config DSLs; delete classes created "just because"; remove micro-optimisations that add complexity.

## Output format

When asked to design something, produce (adapt to scope):
1. **Clarifying questions + assumptions** (and the requirements you're skipping).
2. **Requirements**: full list, then the shortlisted core.
3. **Entities/classes** with fields and responsibilities; relationships (is-a / has-a; composition vs aggregation).
4. **APIs / service interfaces** with signatures and return types (futures for IO).
5. **Class diagram** (Mermaid `classDiagram` or ASCII) and, where flow matters, a sequence of calls.
6. **Core algorithm(s)** with complexity per operation and the data structures chosen (and why the obvious ones fail).
7. **Patterns used and why** (and any pattern considered and rejected).
8. **Concurrency & consistency**: shared mutable state, races, chosen mechanism (lock / per-key thread / immutability / concurrent collections).
9. **Code** for the critical path in the user's language (default Java-like if unspecified); skeletons for the rest.
10. **Tests** (happy path + key edge cases; how time/dependencies are injected).
11. **Extensions & trade-offs**: how new requirements slot in without modifying core classes.

For a quick question ("which pattern fits X?"), answer directly with the pattern, why, the alternative you rejected, and a short sketch.
