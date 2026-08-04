import { LruTtlCache } from './cache.mjs';

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    passed++;
  } else {
    failed++;
    console.log(`FAIL: ${msg}`);
  }
}

// ── Constructor validation ───────────────────────────────────────────
{
  const cache = new LruTtlCache({ capacity: 1 });
  assert(cache instanceof LruTtlCache, "instance check");

  for (const bad of [0, -1, 1.5, "1", null, undefined]) {
    try {
      new LruTtlCache({ capacity: bad });
      assert(false, `capacity=${JSON.stringify(bad)} should throw RangeError`);
    } catch (e) {
      assert(e instanceof RangeError, `capacity=${JSON.stringify(bad)} → RangeError`);
    }
  }

  // Infinity capacity works
  assert(new LruTtlCache({ capacity: 100 }) instanceof LruTtlCache, "large capacity");
}

// ── Injected clock + TTL expiry + has() ─────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 3, defaultTtlMs: 100, now });

  // Basic set/get
  cache.set("a", 1);
  assert(cache.get("a") === 1, "basic get");

  // TTL expiry
  cache.set("b", 2, 50);
  assert(cache.get("b") === 2, "get before expiry");
  t = 1051;
  assert(cache.get("b") === undefined, "get after expiry");

  // has() doesn't affect recency
  // Setup fresh entries with different TTLs
  t = 2000;
  cache.set("a", 1, Infinity);
  cache.set("b", 2, 50);  // expires at 2050
  cache.set("c", 3, Infinity);
  assert(cache.has("b"), "has returns true for live entry at t=2000");
  t = 2051;
  assert(cache.has("b") === false, "has returns false after expiry for b");
  // has(b) removed expired b; a and c should still exist
  assert(cache.has("a"), "has doesn't affect recency of a");
  assert(cache.has("c"), "has doesn't affect recency of c");
}

// ── Capacity + LRU eviction ─────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 2, now });

  cache.set("a", 1);
  cache.set("b", 2);
  assert(cache.get("a") === 1, "get a");
  // a is now MRU, b is LRU
  cache.set("c", 3);
  assert(cache.get("b") === undefined, "LRU evicted");
  assert(cache.get("a") === 1, "a still exists");
  assert(cache.get("c") === 3, "c inserted");
}

// ── Expired eviction before LRU ─────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 2, now });

  cache.set("a", 1, 10);
  cache.set("b", 2, 50);
  t = 1020;
  // a is expired, b is alive
  cache.set("c", 3);
  // Should evict expired "a" first, not "b"
  assert(cache.get("b") === 2, "expired entry evicted before LRU");
  assert(cache.get("c") === 3, "new entry stored");
}

// ── TTL = 0 or negative ────────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 3, now });

  cache.set("z", 999, 0);
  assert(cache.get("z") === undefined, "ttl=0 is immediately expired");
  cache.set("y", 888, -10);
  assert(cache.get("y") === undefined, "ttl=-10 is expired");
}

// ── TTL = Infinity ─────────────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 2, defaultTtlMs: Infinity, now });

  cache.set("x", 100);
  cache.set("y", 200);
  t = 1000000000;
  assert(cache.get("x") === 100, "Infinity TTL never expires");
  assert(cache.get("y") === 200, "Infinity TTL never expires");
}

// ── set updates value + expiry + recency ────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 2, defaultTtlMs: 50, now });

  cache.set("a", 1);
  cache.set("b", 2);
  t = 1040;
  // a is about to expire, but re-set refreshes it
  cache.set("a", 10);
  assert(cache.get("a") === 10, "set updates value");
  t = 1051;
  assert(cache.get("a") === 10, "set refreshes TTL");
}

// ── delete ───────────────────────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 3, now });

  cache.set("x", 1);
  assert(cache.delete("x") === true, "delete returns true");
  assert(cache.delete("x") === false, "delete absent returns false");
}

// ── size ─────────────────────────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 5, defaultTtlMs: 100, now });

  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("c", 3, 50);
  assert(cache.size === 3, "size before expiry");
  t = 1060;
  assert(cache.size === 2, "size after c expired");
}

// ── keys() ───────────────────────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 5, defaultTtlMs: 100, now });

  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("c", 3);
  assert(JSON.stringify(cache.keys()) === JSON.stringify(["c", "b", "a"]),
    "keys() MRU-first");

  cache.get("a"); // bump a to MRU
  assert(JSON.stringify(cache.keys()) === JSON.stringify(["a", "c", "b"]),
    "keys() after get('a')");
}

// ── set returns this ─────────────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 3, now });
  assert(cache.set("a", 1) === cache, "set returns this");
}

// ── has() doesn't affect recency ─────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 2, now });

  cache.set("a", 1);
  cache.set("b", 2);
  cache.get("b");   // bump b to MRU -> order: [a, b] (a=LRU, b=MRU)
  cache.has("a");   // should NOT affect recency
  cache.set("c", 3); // evicts LRU 'a', not 'b'
  assert(cache.get("a") === undefined, "has() didn't affect recency (LRU evicted)");
  assert(cache.get("b") === 2, "b still alive (MRU)");
  assert(cache.get("c") === 3, "c alive");
}

// ── has() removes expired ───────────────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 3, defaultTtlMs: 50, now });

  cache.set("x", 1);
  t = 1060;
  assert(cache.has("x") === false, "has() removes expired");
  assert(cache.size === 0, "size is 0 after purge");
}

// ── Expiry instant counts as expired ─────────────────────────────────
{
  let t = 1000;
  const now = () => t;
  const cache = new LruTtlCache({ capacity: 3, now });

  cache.set("z", 99, 100); // expiry = 1100
  t = 1099;
  assert(cache.get("z") === 99, "get before expiry instant");
  t = 1100;
  assert(cache.get("z") === undefined, "at expiry instant: expired");
}

// ── Summary ──────────────────────────────────────────────────────────
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
