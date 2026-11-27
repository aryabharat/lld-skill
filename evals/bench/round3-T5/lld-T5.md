# Review: NotificationService throttling

**What this change does.** It adds a 60-second per-user throttle in front of email, SMS and push sends. The throttle is one `static HashMap<userId, lastSentMillis>` that all three channels share. If a send arrives inside the window, it is dropped without any signal to the caller.

**Load assumed.** One JVM with many request threads calling the same service at once. I also assume the service may later run on several instances behind a load balancer (see Not checked).

---

## Must fix

**1. Unsynchronised static `HashMap` written from request threads** (`NotificationService`, `lastSent` declaration and the three `put` calls)
- **Problem:** `HashMap` is not thread-safe. If two request threads call `put` while the map resizes, one entry can be lost or the internal table can be corrupted. A reader thread can also see a half-built table. The field is `static`, so every instance and every test shares this mutable state.
- **Fix:** Use a `ConcurrentHashMap` owned by an injected throttle object, not a static field. This change alone does not fix #2.

**2. Check-then-act race sends duplicates** (all three `send*` methods: `getOrDefault` check → `client.send` → `put`)
- **Problem:** Two requests for user U arrive 5 ms apart. Both read "no entry", both pass the check, and U gets two messages. The window is wide because `put` runs only after a network call that can take hundreds of ms. A `ConcurrentHashMap` on its own still races, because the check and the write are separate operations.
- **Fix:** Reserve the slot atomically *before* the IO. If the send throws, give the slot back, so a failed send does not block retries for 60 s:
```java
final class Throttle {
  private final ConcurrentHashMap<String, Long> last = new ConcurrentHashMap<>();
  private final LongSupplier clock;   // System::nanoTime in prod, fake in tests
  private final long windowNanos;
  Throttle(LongSupplier clock, Duration window) { this.clock = clock; this.windowNanos = window.toNanos(); }

  OptionalLong tryAcquire(String key) {
    long now = clock.getAsLong();
    boolean[] granted = {false};
    last.compute(key, (k, prev) -> {
      if (prev != null && now - prev < windowNanos) return prev;
      granted[0] = true;
      return now;
    });
    return granted[0] ? OptionalLong.of(now) : OptionalLong.empty();
  }
  void release(String key, long stamp) { last.remove(key, stamp); }  // only our own stamp
}
```

**3. One throttle key for all channels drops unrelated messages** (`lastSent` keyed by `userId` only)
- **Problem:** `sendEmail(u, "weekly digest")` runs, then 10 s later `sendSms(u, "your OTP is 4821")` is silently dropped. A marketing email suppressing a security SMS is a wrong result. Nothing in the code or the name `lastSent` shows that cross-channel suppression is intended.
- **Fix:** Key by user and channel (`u.getId() + ":" + channel`). If one global per-user cap really is the requirement, keep the `userId` key and name it for that (`lastNotificationAnyChannel`). Either way, write the choice down and test it.

## Should fix

**4. Three copies of the same throttle logic** (`sendEmail`, `sendSms`, `sendPush`)
- **Problem:** Adding WhatsApp means pasting a fourth copy. The race fix above would also need to land in four places, and a sender is deciding *whether* to send, which is a separate concern.
- **Fix:** Keep the public methods so callers stay unchanged, and route them through one private method:
```java
public SendResult sendEmail(User u, String msg) {
  return send(Channel.EMAIL, u, () -> emailClient.send(u.getEmail(), msg));
}
private SendResult send(Channel ch, User u, Runnable call) {
  String key = u.getId() + ":" + ch;
  OptionalLong stamp = throttle.tryAcquire(key);
  if (stamp.isEmpty()) return SendResult.THROTTLED;
  try { call.run(); return SendResult.SENT; }
  catch (RuntimeException e) { throttle.release(key, stamp.getAsLong()); throw e; }
}
```

**5. Silent drop: `void` cannot report "throttled"** (all `send*` signatures)
- **Problem:** A caller sending a password-reset link cannot tell whether it was delivered or swallowed, so it cannot show "try again in a minute" and cannot log it.
- **Fix:** Return a `SendResult` enum (`SENT`, `THROTTLED`). Changing `void` to a return value is source-compatible for existing callers.

**6. Wall clock read inline and twice per operation** (`System.currentTimeMillis()` in the check and in the `put`)
- **Problem:** `currentTimeMillis` jumps when NTP adjusts the clock. A backward step blocks a user for longer than 60 s. A forward step lets a duplicate through. Because the clock is read inline, tests cannot control time.
- **Fix:** Inject a monotonic clock (`System::nanoTime`) and read it once per send, as in #2. Name the window and pass it in through config instead of the literal `60_000`.

**7. Map grows with every user who was ever notified** (`lastSent`, no removal)
- **Problem:** Entries are never removed, so the static map holds one entry for each user notified since the JVM started. It is bounded by the size of the user base but never shrinks, and it is never needed once the window has passed.
- **Fix:** Run a periodic sweep, `last.values().removeIf(t -> now - t >= windowNanos)`, or use a cache with `expireAfterWrite(window)`.

**8. Test depends on the real clock and shared static state, and misses the edges** (`throttles()`)
- **Problem:** The test passes only because both calls run within 60 real seconds. Because the map is static, any other test that uses the same `user` id before this one makes it fail, depending on test order. It does not test that a send succeeds again after the window, the `t == window` boundary, cross-channel behaviour (#3), a failed send releasing the slot, or concurrent sends.
- **Fix:** Build the service with a fake clock and a fresh `Throttle` per test. Add these cases: advance 59 s → throttled; advance to 60 s → sent; email then SMS → per the decision in #3; client throws → next call is sent; N threads send at once to one user → exactly 1 `SENT`.

## Nice to have

9. Rename `lastSent` to say what it is (`lastSentAtByUserChannel`) and replace `60_000` with a named `Duration`.

---

**Verdict:** ship after the must-fixes (#1 to #3). Do #4 at the same time, because it is what keeps the race fix in one place.

**Skipped on purpose**
- A pluggable rate-limit strategy (token bucket, sliding window): the requirement is one message per window, and a fixed gap meets it.
- A Redis-backed distributed throttle: only needed if multi-instance is confirmed (see Not checked).
- Making the sends async: the server is thread-per-request, so synchronous IO on a request thread is normal here. It becomes worth doing only if provider latency starts to exhaust the pool.

**Not checked**
- Whether the web tier runs more than one instance. If it does, each JVM throttles on its own, and a user can get one message per instance per minute. The fix then is a shared store with an atomic set-if-absent-with-TTL (`SET key NX PX 60000`).
- Whether the `emailClient`, `smsClient` and `pushClient` clients are thread-safe and have timeouts. Their code was not part of the diff.
