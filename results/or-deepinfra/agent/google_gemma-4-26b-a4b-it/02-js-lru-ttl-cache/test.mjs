import { LruTtlCache } from './cache.mjs';
import assert from 'node:assert';

async function test() {
  console.log('Starting tests...');

  // 1. Basic Functionality
  {
    const cache = new LruTtlCache({ capacity: 2 });
    cache.set('a', 1);
    cache.set('b', 2);
    assert.strictEqual(cache.get('a'), 1);
    assert.strictEqual(cache.get('b'), 2);
    assert.strictEqual(cache.size, 2);
    // 'a' was accessed, so 'b' is LRU. keys() returns MRU to LRU.
    assert.deepStrictEqual(cache.keys(), ['a', 'b']); 
  }

  // 2. TTL Expiration
  {
    let time = 1000;
    const now = () => time;
    const cache = new LruTtlCache({ capacity: 5, defaultTtlMs: 100, now });

    cache.set('a', 1); // expires at 1100
    assert.strictEqual(cache.get('a'), 1);

    time = 1100;
    assert.strictEqual(cache.get('a'), undefined, 'Should be expired at expiry time');
    assert.strictEqual(cache.size, 0);
  }

  // 3. Capacity and Eviction (LRU vs Expired)
  {
    let time = 1000;
    const now = () => time;
    const cache = new LruTtlCache({ capacity: 2, defaultTtlMs: 100, now });

    cache.set('a', 1); // expires 1100
    cache.set('b', 2); // expires 1100
    
    time = 1050;
    // 'a' is LRU.
    cache.set('c', 3); 
    assert.strictEqual(cache.get('a'), undefined, 'a should have been evicted as LRU');
    assert.strictEqual(cache.get('b'), 2);
    assert.strictEqual(cache.get('c'), 3);

    // Now test purging expired first
    const cache2 = new LruTtlCache({ capacity: 2, defaultTtlMs: 100, now });
    cache2.set('x', 10); // expires 1100
    cache2.set('y', 20); // expires 1100
    
    time = 1101;
    cache2.set('z', 30); // x and y are expired. They should be purged first.
    assert.strictEqual(cache2.size, 1);
    assert.strictEqual(cache2.get('z'), 30);
  }

  // 4. Custom TTL
  {
    let time = 1000;
    const now = () => time;
    const cache = new LruTtlCache({ capacity: 5, defaultTtlMs: 1000, now });

    cache.set('short', 'val', 10); // expires 1010
    cache.set('long', 'val', 5000); // expires 6000

    time = 1010;
    assert.strictEqual(cache.get('short'), undefined);
    assert.strictEqual(cache.get('long'), 'val');
  }

  // 5. Edge Cases
  {
    assert.throws(() => new LruTtlCache({ capacity: 0 }), RangeError);
    assert.throws(() => new LruTtlCache({ capacity: -1 }), RangeError);
    assert.throws(() => new LruTtlCache({ capacity: 1.5 }), RangeError);
  }

  console.log('All tests passed!');
}

test().catch(err => {
  console.error('Test failed!');
  console.error(err);
  process.exit(1);
});
