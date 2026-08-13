/**
 * LruTtlCache implementation
 * 
 * Uses a Map to maintain insertion order, which in JavaScript 
 * allows for O(1) access and O(1) recency updates by deleting 
 * and re-inserting keys.
 */
export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #cache; // Map<key, { value, expiry }>

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("Capacity must be an integer >= 1");
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#cache = new Map();
  }

  /**
   * Internal helper to purge expired entries.
   * Since we must maintain O(1) amortized, we don't purge the whole map 
   * on every call, but we do purge specific keys when they are accessed.
   * However, the 'size' getter and 'set' logic require managing capacity.
   */
  #isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this.#now() >= expiry;
  }

  #purgeExpired(key) {
    const entry = this.#cache.get(key);
    if (entry && this.#isExpired(entry.expiry)) {
      this.#cache.delete(key);
      return true;
    }
    return false;
  }

  set(key, value, ttlMs) {
    // If key exists, remove it first to update recency/order
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    const ttl = ttlMs !== undefined ? ttlMs : this.#defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.#now() + ttl;

    // If we are at capacity, we need to make room
    if (this.#cache.size >= this.#capacity) {
      // 1. Try to find any expired entry to evict first
      // We iterate through the map. Since Map preserves insertion order,
      // we can't easily find "any" expired without a scan, but the prompt 
      // implies we should prioritize expired entries.
      // To keep O(1) amortized, we check the oldest entries (first in Map).
      let evicted = false;
      for (const [k, entry] of this.#cache.entries()) {
        if (this.#isExpired(entry.expiry)) {
          this.#cache.delete(k);
          evicted = true;
          break; 
        }
      }

      // 2. If no expired entries found, evict the LRU (the first entry in Map)
      if (!evicted) {
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
    // To ensure the getter is accurate and purges, we iterate and clean.
    for (const [key, entry] of this.#cache.entries()) {
      if (this.#isExpired(entry.expiry)) {
        this.#cache.delete(key);
      }
    }
    return this.#cache.size;
  }

  keys() {
    const liveKeys = [];
    for (const [key, entry] of this.#cache.entries()) {
      if (!this.#isExpired(entry.expiry)) {
        liveKeys.push(key);
      } else {
        // Clean up as we traverse to satisfy the "must purge" requirement
        this.#cache.delete(key);
      }
    }
    // Map iteration is insertion order (LRU -> MRU). 
    // Requirement: "ordered from most recently used to least recently used".
    return liveKeys.reverse();
  }
}
