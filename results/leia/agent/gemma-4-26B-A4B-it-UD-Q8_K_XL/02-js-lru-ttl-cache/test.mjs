import { LruTtlCache } from './cache.mjs';
import assert from 'node:assert';

function test() {
  let currentTime = 1000;
  const now = () => currentTime;

  // 1. Basic functionality
  const cache = new LruTtlCache({ capacity: 3, defaultTtlMs: 100, now });
  cache.set('a', 1);
  cache.set('b', 2);
  assert.strictEqual(cache.get('a'), 1);
  // MRU to LRU: a is MRU because of get('a'). Map order: b, a.
  // keys() returns reverse: ['a', 'b'].
  assert.deepStrictEqual(cache.keys(), ['a', 'b']);

  // 2. TTL Expiry
  currentTime += 50;
  assert.strictEqual(cache.get('a'), 1);
  currentTime += 60; // a expires at 1100. Now 1110.
  assert.strictEqual(cache.get('a'), undefined);
  assert.strictEqual(cache.size, 0);

  // 3. Capacity and Eviction
  const cache2 = new LruTtlCache({ capacity: 2, defaultTtlMs: 100, now });
  cache2.set('x', 10); // expiry 1100
  cache2.set('y', 20); // expiry 1100
  currentTime = 1050;
  cache2.set('z', 30); // capacity reached. 
  // Check for expired: x and y expire at 1100. None are expired yet.
  // Evict LRU: x is LRU.
  // Cache should have y, z.
  assert.strictEqual(cache2.get('x'), undefined);
  assert.strictEqual(cache2.get('y'), 20);
  assert.strictEqual(cache2.get('z'), 30);

  // 4. Evict expired first
  const cache3 = new LruTtlCache({ capacity: 2, defaultTtlMs: 100, now });
  cache3.set('a', 1); // expiry 1100
  cache3.set('b', 2); // expiry 1100
  currentTime = 1150; // both expired
  cache3.set('c', 3); // should purge expired first.
  assert.strictEqual(cache3.size, 1);
  assert.strictEqual(cache3.get('c'), 3);

  // 5. Custom TTL
  const cache4 = new LruTtlCache({ capacity: 5, defaultTtlMs: 1000, now });
  cache4.set('short', 1, 10); // expiry 1010
  cache4.set('long', 2, 1000); // expiry 2000
  currentTime = 1050;
  assert.strictEqual(cache4.get('short'), undefined);
  assert.strictEqual(cache4.get('long'), 2);

  // 6. RangeError
  assert.throws(() => new LruTtlCache({ capacity: 0 }), RangeError);
  assert.throws(() => new LruTtlCache({ capacity: -1 }), RangeError);
  assert.throws(() => new LruTtlCache({ capacity: 1.5 }), RangeError);

  console.log("All tests passed!");
}

try {
  test();
} catch (e) {
  console.error("Test failed:");
  console.error(e);
  process.exit(1);
}
