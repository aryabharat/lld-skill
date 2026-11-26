# Grading rubric (judges only)

You are grading anonymous answers (A-F) to one task. Answers came from the same model with different instructions. Judge only what is written. Do not reward length for its own sake; reward correct, decision-useful content a senior reviewer would want. Penalise errors, over-engineering, and padding.

For each answer give:
1. **Checklist**: 1 or 0 for each item listed for the task below (partial = 0).
2. **Scores 1-10**: Correctness (no bugs, races or wrong claims), Design quality (right structure, right owner, extensible where it needs to be and simple where it does not), Decision clarity (states the choice, the rejected options and when the choice would flip), Proportionality (length and depth fit the question; 10 = exactly right-sized).
3. **Errors**: list any technical mistakes (concurrency bugs, wrong complexity, code that would not work).
Then rank all answers 1 (best) to N.

## Checklists

**T1**
- Pricing rules are pluggable objects (strategy/rule list/table), not vehicle or day subclasses and not one growing switch
- Handles rule combination/ordering explicitly (stacking, order of adjustments)
- Time/date is injected (clock or argument), not read inside the pricing logic
- Spot allocation is atomic so two concurrent requests can never get the same spot, with a correct mechanism
- Explains why the chosen concurrency mechanism is correct (or why a naive one fails)
- Money handled safely (integer minor units or BigDecimal, not double)
- Tests are deterministic and include a concurrency test or a fixed-time pricing test
- Names at least one rejected alternative with a reason

**T2**
- Identifies that the if-chain must be edited for every new rule (open-closed problem) or justifies a minimal change explicitly
- Proposes rules as objects in an ordered list (or justifies keeping if/else)
- Win checks are evaluated before the move-limit draw (order made explicit)
- Move count is owned by the board/game state, not computed ad hoc
- Limit is configurable, not hard-coded inside the rule
- Mentions or writes tests (49 vs 50 moves, win on the 50th move)

**T3**
- Says no
- Gives the reason (two required fields; constructor/record is clearer)
- States when Builder would start to pay off
- Answer is short (under ~250 words)

**T4**
- Makes a reasoned judgement on State (not reflexive yes), based on whether states have distinct behaviour
- Enforces legal transitions in one place (transition table/enum/state classes)
- Uses Observer/events for notifications with multiple, growing subscribers
- Records status history or handles concurrent status updates (conditional update/versioning)
- Says when the alternative (State) would become worth it

**T5**
- Flags the unsynchronised static HashMap / check-then-act race with a concrete consequence
- Notes the throttle key is shared across channels (email blocks SMS) or questions it
- Proposes collapsing the three near-identical methods (channel abstraction/strategy)
- Flags System.currentTimeMillis in logic/test as non-deterministic; proposes an injected clock
- Notes unbounded map growth (memory leak) or static state shared across instances/tests
- Notes the send happens before the timestamp is recorded / failure handling
- Findings are prioritised by severity

**T6**
- Correct TTL handling (expiry checked on read and/or purged; based on write/load time)
- Correct O(1) or O(log n) LRU structure with eviction at capacity
- All index structures stay consistent under concurrency (no race between map and LRU order)
- Slow load does not block other keys / does not hold a global lock during the 50 ms load
- Concurrent misses for the same key load once (request collapsing / computeIfAbsent future)
- Code would actually work (no obvious bugs)
- States trade-offs (global lock vs striping, write policy) explicitly

**T7**
- Membership as rows in a join table with a role, not lists in a column
- Teams modelled with team membership and repo grants to teams
- Repository access grant table(s) covering user and team grants with permission level
- Primary/unique keys prevent duplicate memberships/grants
- Indexes justified by named queries (e.g. "repos a user can access", "members of org")
- Considers access resolution (user direct + via team) or a check query

**T8**
- Each discount becomes its own rule object implementing a common interface
- Adding a rule does not require editing the calculator
- Handles non-stacking/exclusivity explicitly (groups, priority, or best-of)
- Returns which rules applied (result object / applied list) for finance
- Money not in double, or flags it
- Time/date and user history not read implicitly in a way that hurts testing, or tests shown
- Keeps the 30% cap as an explicit policy
