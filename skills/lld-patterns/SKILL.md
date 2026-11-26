---
name: lld-patterns
description: >
  Pick, or reject, a design pattern for a concrete situation: Strategy, State,
  Factory, Builder, Prototype, Singleton, Observer / pub-sub, Command, Chain of
  Responsibility, rule engine, Template method, Memento, Proxy, Flyweight,
  object pool, Iterator, keyed executor, retry policy. Use when the user asks
  "which pattern fits", "should I use X pattern here", "is this over-engineered",
  "strategy or state", "observer or direct call", or shows code with a growing
  if/else, switch on type, constructor overloads or duplicated variants.
license: MIT
---

# LLD patterns

Read the picker table at the top of [patterns.md](../lld/references/patterns.md), then the entries it points to. Use [principles-and-smells.md](../lld/references/principles-and-smells.md) when the root problem is a principle (SRP, OCP, LSP) rather than a pattern.

## Answer shape

1. **The problem in one line**: the signal you see (if-chain that every feature edits, constructor overloads multiplying, recipients that change at runtime...). If there is no real problem, say "no pattern needed" and stop there; that is a valid answer.
2. **Pick**: the pattern, why it removes this problem, and what changes when the next variant arrives.
3. **Rejected**: the closest alternative and why it loses here. Always give one.
4. **Sketch**: at most 15 lines in the user's language, showing only the shape.
5. **Watch out**: the pitfall the course hit with this pattern (order-dependent rules in a rule list, a base builder that returns the base type, Observer used for a single fixed recipient, State copying the global if/else into every class).

Keep it short. Go to the full design format only if the user asks for the whole design.
