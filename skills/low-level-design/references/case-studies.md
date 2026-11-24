# Worked case studies (condensed)

## Turn-based game engine (the course's running project)
- Classes: GameEngine (start, move), RuleEngine (getState via RuleSet per board type), AIEngine (suggestMove via Strategy/Chain), Board interface {move, copy} -> CellBoard {getSymbol} -> TicTacToeBoard (+getRules), Move {player, cell}, Player {symbol, timeUsed; flip()}, User {id, stats}, Cell (shared flyweights), GameState/GameInfo (builder), Game {board, config, lastMoveTime; move(move, timestamp)}, GameConfig {timed, maxTimePerMove, maxTimePerPlayer}, GameFactory, History (memento), placements chain (Offensive -> Defensive -> Fork -> Center -> Corner), notifications via EventBus + commands.
- Key lessons: SRP split; rules as data; prototype for look-ahead; composition for timed games; ISP for CellBoard; deterministic tests; pub-sub for notifications.

## Tic-tac-toe interview
- Board int[n][n] (+1/-1), winner, current player, `int move(player,row,col)`. O(1) win check with running row/col/diag sums (|sum| == n). Game keeps moves list for replay/undo.

## Chess
- Abstract Piece with template `move(start,end)`: reject own-colour destination; simulate on temp board; reject if own king in check; capture; flag enemy check; abstract `isValidMove`, `getAllPossibleMoves`. Board {Map<Position,Piece>}; Color enum. Pawn double move derived from rank; castling/en passant/promotion as special behaviours - clarify scope.

## Splitwise
- Expense {id, BalanceMap userId->Amount, metadata, settled, groupId}; Group {id, userIds}; GroupExpenses separate (deliberate denormalisation); Amount immutable; PaymentGraph {Map<userId, BalanceMap>}.
- GroupService.getGroupPaymentGraph(groupId, userId): authorise -> ExpenseService.getGroupExpenses -> sum per user -> getPaymentGraph.
- Greedy simplification: two max-heaps (creditors/debtors), settle min(top credit, top debt), push remainder. Not optimal (subset-sum is); fine for interviews.
- Cache group balances & graph; immutability + reference swap for consistent reads.

## Cache (machine coding)
- API: `CompletableFuture<V> get(K)`, `CompletableFuture<Void> set(K,V)`. DataSource {load, persist}. Requirements: read-your-writes, write-through/back, TTL, LRU/LFU, request collapsing, hot loading, event logging.
- Map<K, CompletableFuture<Record<V>>>; Record {value, loadTime, AccessDetails{accessTimestamp, accessCount}}.
- Indexes: expiryQueue ConcurrentSkipListMap<loadTime, List<Record>>; priorityQueue ConcurrentSkipListMap<AccessDetails, List<K>> with comparator (LRU by time; LFU by count, ties LRU).
- Before every addToCache: if full, lazily purge expired from expiry index; if still full evict one key from first priority bucket; keep both indexes in sync.
- Per-key single-thread executors; write-through composes persist then cache; write-back caches then fires persist.

## Event bus (machine coding)
- Event {id, name, attributes, timestamp}; Topic, EventId, EntityId wrappers; Subscription {id, subscriberId, topic, PULL|PUSH, precondition, handler}.
- Structures per topic: event list; eventIndexes (id -> index, O(1)); timestamps ConcurrentSkipListMap (ts -> index, O(log n) higherEntry); subscriberIndexes ((topic, subscriber) -> index).
- APIs: publish (O(log n)), poll (O(1)), getEvents(t1,t2), setIndexAfterTimestamp, setIndexAfterEvent.
- Threads: writes hash(topic); reads hash(topic, subscriber). Push via RetryAlgorithm; failures -> DLQ bus. Idempotent publish by event id. No update/delete.

## Message queue (live)
- API first: addToQueue(topic, msg), register(topic, subscriber) for push only, poll(topic, subscriber). Map<topicId, Topic{pullOffsets, pushSubscribers, messages}>; offsets kept by the queue; push with retries/backoff -> DLQ; back pressure for push; soft deletes; persist synchronously before ack.

## Rate limiter (machine coding)
- Client library (fast local decision, pluggable algorithm with SlidingWindow default, onAccept/onReject callbacks returning futures, own small executor for server IO) + simple server (configs (service, key, timeUnit, limit) in DB, aggregated heartbeats, DAO layering, gateway thread pool). Fail open if server unreachable.
- Sliding window: list of timestamps; evict older than window; accept if size < threshold. Back pressure decreases threshold on rejects; forward pressure tiny.
- Generic key instead of a config DSL (userId_date).

## Google logger (start/end/poll)
- Map<id, Process> + ConcurrentSkipListMap<startTime, Process>; poll prints head only if ended; futures for blocking poll completed by end; ReentrantLock on poll/end; per-process executor ordering start before end; concurrency tests with random interleavings.

## Orchestration service
- Validate -> decode params -> dependency table -> topological sort of services -> call in order passing outputs -> response. Services as interfaces; write lock on dependency table updates.

## Google Calendar
- Create/update/getEvents(range). Participants join table (userId, eventId, status, joinedAt). Recurring events as blueprints with cron-like rules, generated on read; splits via ending blueprint + cloning (prototype) for "this and following"/"just this"; exponential + binary search to first occurrence in a far range. Client-generated ids for idempotency (Snowflake-style).

## Stock trading (Zerodha)
- Entities Stock, User (wallet, Portfolio, Watchlist, ActiveOrders), Order {stock, user, price, qty, isBuy, OrderType, OrderState}, Portfolio {Map<Stock, PortfolioStock{qty, avgPrice}>}. Services User/Stock/Order/Notification + ValidationEngine. Strategy for buy vs sell; market vs limit; Observer only for multi-subscriber status fan-out; prices pushed over websocket subscriptions.

## Twitter
- Profile, Tweet, Comment, Reaction; abstract Reactable/Commentable; services Profile/Tweet/Comment/Reaction/Timeline/Trending. Hybrid fan-out: push for normal users, pull celebrities on open with binary search from lastSeen; trending triggered by the service owning the metric (reaction count threshold).

## Live scores (Cricbuzz)
- One-way real-time -> SSE (or long polling); websockets overkill; LRU-evict connections; avoid thundering herds; scale out on thrashing.

## Coupon engine (Zomato)
- applyCoupon(proposed, cart, applied) -> {applied set, deducted, cashback}; getCoupons(cart). Rules as stored function objects (AND); admin dashboard + few system coupons in code; index userId/restaurantId/platform/validity outside the rule blob; usage limits via order/coupon-usage table.

## Zomato delivery assignment (mock)
- getOrderStatus + assignDeliveryExecutive (sequential offers with timeout, not broadcast; delay assignment while cooking); status enum + status log; Observer for status changes; object/connection pools for shared resources.

## GitHub / DB schema
- Product-first schema; normalised org membership rows (or split admin/member tables by access pattern); ACL tuples (Zanzibar-like user sets); content-addressed objects (hash -> location), trees list children, refs (project, branch) -> root hash; persistent structure sharing; reframe "load whole repo" (only on clone).
