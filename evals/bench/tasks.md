# LLD benchmark tasks

Answer each task independently, as a senior engineer would in a design doc or PR comment. Use Java unless the task says otherwise.

## T1 Parking lot pricing and allocation
A multi-floor parking lot. The fee depends on vehicle type (bike, car, truck) and on weekday vs weekend; product says more pricing rules are coming (night rate, member discount, event surcharge). Several entry gates run concurrently and two cars can request a spot at the same moment. Design the fee calculation and spot allocation. Give the key classes, interfaces and code for the critical path, and the tests you would write.

## T2 Feature on existing code
```java
class GameEngine {
  GameState getState(Board b) {
    if (rowWin(b)) return GameState.win(b.lastPlayer());
    if (colWin(b)) return GameState.win(b.lastPlayer());
    if (diagWin(b)) return GameState.win(b.lastPlayer());
    if (revDiagWin(b)) return GameState.win(b.lastPlayer());
    if (b.isFull()) return GameState.draw();
    return GameState.inProgress();
  }
}
```
Add: the game is a draw after 50 moves without a win. Show the change you would make.

## T3 Pattern restraint
Should I use the Builder pattern for a `Point` class with `x` and `y`?

## T4 State pattern question
Order status goes PLACED -> CONFIRMED -> COOKING -> PICKED -> DELIVERED, and can be CANCELLED from PLACED, CONFIRMED or COOKING. On every change we notify the customer and the restaurant, and analytics may subscribe later. Should I use the State pattern? Show the design you would pick.

## T5 Review this diff
```java
public class NotificationService {
  private static Map<String, Long> lastSent = new HashMap<>();   // userId -> epoch ms

  public void sendEmail(User u, String msg) {
    if (System.currentTimeMillis() - lastSent.getOrDefault(u.getId(), 0L) < 60_000) return;
    emailClient.send(u.getEmail(), msg);
    lastSent.put(u.getId(), System.currentTimeMillis());
  }
  public void sendSms(User u, String msg) {
    if (System.currentTimeMillis() - lastSent.getOrDefault(u.getId(), 0L) < 60_000) return;
    smsClient.send(u.getPhone(), msg);
    lastSent.put(u.getId(), System.currentTimeMillis());
  }
  public void sendPush(User u, String msg) {
    if (System.currentTimeMillis() - lastSent.getOrDefault(u.getId(), 0L) < 60_000) return;
    pushClient.send(u.getDeviceToken(), msg);
    lastSent.put(u.getId(), System.currentTimeMillis());
  }
}

@Test void throttles() {
  service.sendEmail(user, "a");
  service.sendEmail(user, "b");
  assertEquals(1, fakeEmail.sent.size());
}
```
This service is called from a web server's request threads. Review it.

## T6 In-process cache
Implement the core of an in-process cache in Java with per-entry TTL and LRU eviction at a fixed capacity, safe under concurrent `get`/`put` from many threads, backed by a slow database (`load(key)` takes ~50 ms). Show the data structures, the key code, and how you handle concurrency.

## T7 Schema
Design the relational schema for GitHub-style organisations: users belong to organisations as members or admins, organisations own repositories, and access to a repository can be granted to a user or to a team. Show the tables, keys and the indexes you would add, and why.

## T8 Refactor a growing class
```java
class DiscountCalculator {
  double discount(Order o) {
    double d = 0;
    if (o.user().isPremium()) d += o.total() * 0.10;
    if (o.total() > 1000) d += 50;
    if (o.coupon() != null && o.coupon().equals("WELCOME")) d += o.total() * 0.05;
    if (o.coupon() != null && o.coupon().equals("FESTIVE") && o.date().getMonth() == Month.OCTOBER) d += 100;
    if (o.user().orders() == 0) d += 25;
    return Math.min(d, o.total() * 0.30);
  }
}
```
Marketing adds a new discount rule roughly every week, some rules must not stack with others, and finance wants to know which rules applied to each order. Refactor.
