# Problem 2 — LRU Cache with TTL (JavaScript, medium)

Write a JavaScript (Node.js, ES modules) implementation in a single file named
`cache.mjs` that exports a class:

```js
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) { ... }
}
```

An LRU (least-recently-used) cache where every entry also has a time-to-live.
The `now` option is an injected clock function returning milliseconds; **all
time arithmetic must use it** (never call `Date.now()` directly), so the cache
is testable with a fake clock.

## Required API

- `constructor({ capacity, defaultTtlMs, now })` — `capacity` must be an
  integer ≥ 1, otherwise throw `RangeError`.
- `set(key, value, ttlMs?)` — insert or replace. The entry expires at
  `now() + (ttlMs ?? defaultTtlMs)`. Setting an existing key updates its
  value, its expiry, and makes it the most recently used. Returns `this`.
- `get(key)` — returns the value and makes the entry most recently used.
  Returns `undefined` if the key is absent **or expired**. An expired entry
  must be removed when discovered.
- `has(key)` — `true` if present and not expired; does **not** affect
  recency. Removes the entry if it is discovered to be expired.
- `delete(key)` — removes the entry; returns `true` if something was removed.
- `size` (getter) — number of **live** (non-expired) entries. Must not count
  entries whose TTL has passed, and must purge them.
- `keys()` — array of live keys ordered from most recently used to least
  recently used.

## Semantics

1. Keys are compared like `Map` keys (any value, SameValueZero).
2. When a `set` would grow the cache beyond `capacity`, evict expired entries
   first; if still over capacity, evict the least recently used entry.
3. An entry with `ttlMs` of `Infinity` never expires.
4. An entry is expired when `now() >= expiryTime` (expiry instant itself
   counts as expired), except `Infinity` never expires.
5. `ttlMs` of `0` or negative means the entry is already expired.

## Constraints

- No dependencies; Node standard library only (you likely need none).
- Node 20+ ES module (`.mjs`, `export class`).
- `get`, `set`, `has`, `delete` should be O(1) amortized (a `Map` keeps
  insertion order — that is enough; do not use arrays for recency).

**Deliverable: exactly one file, `cache.mjs`.**
