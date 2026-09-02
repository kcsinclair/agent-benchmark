/**
 * LruTtlCache implementation.
 * Uses a Map to maintain insertion order for LRU semantics.
 * In JavaScript, Map.prototype.keys() returns keys in insertion order.
 * By deleting and re-setting a key, we move it to the "most recent" position.
 */
export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #cache; // Map<key, { value, expiry }>

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("Capacity must be an integer >= 1");
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#cache = new Map();
  }

  /**
   * Internal helper to check if an entry is expired.
   * @param {number} expiry 
   * @returns {boolean}
   */
  #isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this.#now() >= expiry;
  }

  /**
   * Internal helper to purge expired entries to free up space or maintain size accuracy.
   * This is called during size access and set operations.
   */
  #purgeExpired() {
    for (const [key, entry] of this.#cache.entries()) {
      if (this.#isExpired(entry.expiry)) {
        this.#cache.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const expiry = this.#now() + (ttlMs ?? this.#defaultTtlMs);

    // If key exists, remove it first to update its position in Map (recency)
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    // If at capacity, we must make room
    if (this.#cache.size >= this.#capacity) {
      // 1. Try to find an expired entry to evict
      let evictedExpired = false;
      for (const [k, entry] of this.#cache.entries()) {
        if (this.#isExpired(entry.expiry)) {
          this.#cache.delete(k);
          evictedExpired = true;
          break; // Evict one expired entry
        }
      }

      // 2. If no expired entry found, evict the Least Recently Used (first in Map)
      if (!evictedExpired) {
        const firstKey = this.#cache.keys().next().value;
        this.#cache.delete(firstKey);
      }
    }

    this.#cache.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this.#cache.get(key);

    if (!entry) return undefined;

    if (this.#isExpired(entry.expiry)) {
      this.#cache.delete(key);
      return undefined;
    }

    // Refresh recency: delete and re-insert
    this.#cache.delete(key);
    this.#cache.set(key, entry);

    return entry.value;
  }

  has(key) {
    const entry = this.#cache.get(key);

    if (!entry) return false;

    if (this.#isExpired(entry.expiry)) {
      this.#cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this.#cache.delete(key);
  }

  get size() {
    // The requirement states size must not count expired entries and must purge them.
    this.#purgeExpired();
    return this.#cache.size;
  }

  keys() {
    const liveKeys = [];
    // We iterate through the map. Since Map maintains insertion order,
    // and we move items to the end on 'get'/'set', the order is LRU -> MRU.
    // The requirement asks for MRU to LRU.
    
    // First, purge to ensure we only return live keys
    this.#purgeExpired();

    // Map.keys() is LRU -> MRU. We need MRU -> LRU.
    const allKeys = Array.from(this.#cache.keys());
    return allKeys.reverse();
  }
}
