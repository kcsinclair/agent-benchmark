/**
 * LruTtlCache implementation.
 * Uses a Map to maintain insertion order, which in JavaScript 
 * allows for O(1) access and O(1) "move to end" (by deleting and re-setting).
 */
export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #cache; // Map<key, { value, expiry }>

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("capacity must be an integer ≥ 1");
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#cache = new Map();
  }

  /**
   * Internal helper to purge expired entries.
   * Note: To maintain O(1) amortized complexity, we don't purge the whole map
   * every time, but we do purge the specific key being accessed or when capacity is hit.
   */
  #isExpired(expiry) {
    return expiry !== Infinity && this.#now() >= expiry;
  }

  /**
   * Removes an entry from the map.
   * @param {*} key 
   * @returns {boolean} true if an entry was removed.
   */
  delete(key) {
    return this.#cache.delete(key);
  }

  /**
   * Inserts or replaces a value.
   * @param {*} key 
   * @param {*} value 
   * @param {number} [ttlMs] 
   * @returns {LruTtlCache}
   */
  set(key, value, ttlMs) {
    // If key exists, remove it first to update recency (move to end of Map)
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiry = this.#now() + ttl;

    // If the new entry is already expired (ttl <= 0), don't even add it
    if (this.#isExpired(expiry)) {
      return this;
    }

    this.#cache.set(key, { value, expiry });

    // Handle capacity
    if (this.#cache.size > this.#capacity) {
      // 1. Try to find and evict an expired entry first to make room
      // We iterate through the Map (oldest to newest)
      for (const [k, entry] of this.#cache.entries()) {
        if (this.#isExpired(entry.expiry)) {
          this.#cache.delete(k);
          break; 
        }
      }

      // 2. If still over capacity, evict the Least Recently Used (the first entry in Map)
      if (this.#cache.size > this.#capacity) {
        const firstKey = this.#cache.keys().next().value;
        this.#cache.delete(firstKey);
      }
    }

    return this;
  }

  /**
   * Returns the value and makes the entry most recently used.
   * @param {*} key 
   * @returns {*}
   */
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

  /**
   * Returns true if present and not expired.
   * @param {*} key 
   * @returns {boolean}
   */
  has(key) {
    const entry = this.#cache.get(key);

    if (!entry) return false;

    if (this.#isExpired(entry.expiry)) {
      this.#cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Returns the number of live (non-expired) entries.
   * Purges expired entries during the count.
   * @returns {number}
   */
  get size() {
    const currentTime = this.#now();
    for (const [key, entry] of this.#cache.entries()) {
      if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
        this.#cache.delete(key);
      }
    }
    return this.#cache.size;
  }

  /**
   * Returns keys ordered from most recently used to least recently used.
   * @returns {Array<*>}
   */
  keys() {
    const currentTime = this.#now();
    const liveKeys = [];
    
    // Map.keys() returns insertion order (LRU is the start, MRU is the end)
    // We need MRU -> LRU, so we iterate backwards or reverse.
    // However, we must only include live keys.
    const entries = Array.from(this.#cache.entries());
    
    // Iterate backwards to get MRU first
    for (let i = entries.length - 1; i >= 0; i--) {
      const [key, entry] = entries[i];
      if (entry.expiry === Infinity || currentTime < entry.expiry) {
        liveKeys.push(key);
      }
    }
    
    return liveKeys;
  }
}
