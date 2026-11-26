# Eval cases

Each case is a prompt plus the behaviours a good answer must show, taken from the course's rules. Run each prompt with and without the plugin and score one point per behaviour present. `scripts/` does not automate this; run it by hand or with your harness of choice.

## 1. Parking lot fees (pattern fit + concurrency)
Prompt: "Parking lot: fee depends on vehicle type and weekday vs weekend, and more rules are coming. Two cars can arrive at the same gate at once. Design the fee calculation and spot allocation in Java."
Must show:
- fee rules as strategy objects or a rule list, not subclasses like WeekendCarTicket and not one growing switch
- a rejected alternative named with a reason
- time injected (clock or timestamp argument), not `LocalDateTime.now()` inside the rule
- spot allocation made atomic (lock over the free-spot structure, keyed executor per floor/pool, or atomic remove), and states why per-structure thread safety alone is not enough
- a test with fixed timestamps

## 2. Adding a feature to existing code (OCP)
Prompt: give a `GameEngine.getState()` with six `if (...) return` checks and ask "add a rule for a draw after 50 moves".
Must show:
- recognises the if-chain every feature edits as the smell
- moves to a list of Rule objects, OR keeps if/else because the rules are order-dependent, and says which and why
- does not add a wrapper layer around the existing method

## 3. Cache with TTL and LRU (data structures + threads)
Prompt: "Implement an in-process cache with TTL and LRU eviction, safe for concurrent get/set, backed by a slow DB."
Must show:
- TTL measured from load time in its own index, separate from the LRU index
- both indexes updated on every insert, evict and expiry path
- expired entries purged before evicting a live key
- reads/writes for one key ordered (per-key single-thread executor or equivalent), other keys parallel
- get/set return futures; DB calls off the request thread
- request collapsing for concurrent misses (or named as an extension)
- write-through vs write-back stated as a choice

## 4. Review a diff (review skill)
Prompt: a `NotificationService` with `sendEmail(User)`, `sendSms(User)`, `sendPush(User)` (identical bodies apart from the channel), a `static Map` shared across threads, and a test that calls `System.currentTimeMillis()`.
Must show:
- findings grouped Must / Should / Nice
- the shared map race as Must fix with a concrete interleaving
- the three near-identical methods collapsed behind one method plus a channel strategy or command
- the clock in the test flagged
- at least one suggestion explicitly skipped as not worth it

## 5. Over-engineering restraint
Prompt: "Should I use the Builder pattern for a Point class with x and y?"
Must show:
- says no, with the reason (two required fields; a constructor is clearer)
- names when Builder would start to pay (several optional fields, overloads multiplying)

## 6. Pattern rejection (State)
Prompt: "Order status goes PLACED -> CONFIRMED -> COOKING -> PICKED -> DELIVERED, can be CANCELLED from the first three, and notifies the customer and the restaurant on each change. Use the State pattern?"
Must show:
- a judgement on State based on the transition graph and per-state behaviour, not a reflex yes
- an enum with a transition table, plus a status log, is offered as the simpler choice if states have little behaviour
- Observer/events for the notifications to several subscriber types

## 7. Schema from features
Prompt: "Design the tables for GitHub organisations with members and admins, and repository access."
Must show:
- no lists stored in a single column
- membership as rows (or admin/member tables split by access pattern), with the reason coming from queries
- indexes chosen from the queries named

## 8. Interview mode
Prompt: "mock interview me on a rate limiter, 45 minutes"
Must show:
- an underspecified prompt, answers to clarifying questions only when asked
- at least one probe each on scope, concurrency and a new requirement
- feedback with positives, gaps, and a hire signal
