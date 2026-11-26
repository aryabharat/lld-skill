---
name: lld-review
description: >
  Design review of code changes or a proposed design against the LLD course's
  rules: class responsibilities, naming, inheritance misuse, open-closed
  violations, pattern misfit, data-structure cost, thread safety, blocking IO,
  retries, schema and test determinism. Use when the user asks to review a diff,
  PR, branch, files, class diagram or design doc for design quality, or says
  "lld review", "design review", "is this well designed", "is this thread-safe".
  Reports findings; changes no code unless asked.
license: MIT
---

# LLD review

Review like the senior engineer who will have to add the next three features to this code. Read the [review checklist](../lld/references/review-checklist.md) and the smell table in [principles-and-smells.md](../lld/references/principles-and-smells.md) first; open [concurrency-and-async.md](../lld/references/concurrency-and-async.md) if the change touches threads, futures, caches, queues or locks.

## Scope

Review what the user names (diff, staged changes, branch, PR, files, a pasted design). Nothing named: the uncommitted changes, else the last commit. Read the callers of every changed function, the functions it calls, and the tests. A change can break code it does not touch.

## Look for, in this order

1. **Correctness**: wrong result, missed edge case, validation missing at the entry point, invariants not kept (sums, indexes out of sync, both indexes not updated).
2. **Concurrency and IO**: unguarded shared state, check-then-act races, per-structure thread safety assumed to make a composite safe, lock held while waiting on a future, a socket-reader or event-loop thread blocked on IO (synchronous IO in a thread-per-request server is normal), ordering assumed from a thread pool, retries on non-retryable errors, no idempotency.
3. **Extensibility**: a new variant added by editing a tested switch/if-chain, a member on a base type that some subtype cannot honour, a flag modelled as a subclass, duplicated methods differing only by parameter type, a central class every feature must edit.
4. **Objects and naming**: names that lie, god classes, parallel maps keyed alike, nested maps, data owned by the wrong class, booleans where a result object is needed.
5. **Data structures**: an operation that is O(n) where the API needs O(log n) or O(1); hash maps used for range or nearest lookups; lists in DB columns.
6. **Tests**: system clock in tests, assertions coupled to a changeable algorithm, missing tests for risky logic.
7. **Over-engineering**: a pattern with no problem behind it, a DSL where a key works, a micro-optimisation that hurts reading. Removing it is a valid finding.

Every finding needs a concrete case (input, interleaving, or the next feature that breaks it). Re-read the lines to confirm. No style taste, no vague worries.

**Severity discipline.** Must fix = wrong results, races that corrupt or double-act, data loss, leaks that grow without bound, security. A design rule the diff breaks without an observed failure (sync IO on a request thread, a missing abstraction) is Should fix at most, and the fix must keep the caller's contract unless you say why it has to change. Stay inside the diff: do not turn a review into a redesign. Fix sketches must compile and must handle a synchronous throw as well as a failed future.

**Length.** Under ~900 words. One line per Nice to have. Do not restate the rules file; cite the rule in a few words.

## Output

Start with **What this change does** in two or three sentences, and the load you assumed (single process, many threads, many instances).

Then numbered findings grouped **Must fix / Should fix / Nice to have**. Each finding:

- **Title** with `file:lines`
- **Problem**: what goes wrong, with the concrete case
- **Fix**: the smallest change that stays inside the diff, with a short sketch when it helps; name the principle or pattern in a few words only if it explains the fix

End with **Verdict** (ship / ship after must-fixes / redesign), **Skipped on purpose** (suggestions you considered and rejected as not worth it, with why), and **Not checked** if something mattered and you could not check it. Nothing found: "Looks good. Ship."

Change no code unless the user asks for fixes.
