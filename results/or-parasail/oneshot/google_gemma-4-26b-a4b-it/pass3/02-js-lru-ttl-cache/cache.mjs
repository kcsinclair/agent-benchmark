/**
 * LruTtlCache implementation
 * 
 * Uses a Map to maintain insertion order, which in JavaScript allows for 
 * O(1) access and O(1) updates to recency by deleting and re-inserting.
 * The Map's iterator follows insertion order (oldest to newest).
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
   * Internal helper to check if an entry is expired.
   * @param {number} expiry 
   * @returns {boolean}
   */
  #isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this.#now() >= expiry;
  }

  /**
   * Internal helper to purge all expired entries currently in the Map.
   * This is called during size access and set operations to ensure accuracy.
   */
  #purgeExpired() {
    for (const [key, entry] of this.#cache.entries()) {
      if (this.#isExpired(entry.expiry)) {
        this.#cache.delete(key);
      }
    }
  }

  /**
   * Returns the number of live (non-expired) entries.
   * Purges expired entries before returning.
   */
  get size() {
    this.#purgeExpired();
    return this.#cache.size;
  }

  /**
   * Inserts or replaces an entry.
   * Updates recency and expiry.
   */
  set(key, value, ttlMs) {
    // If key exists, remove it first to update recency via re-insertion
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.#now() + ttl;

    // If the new entry is already expired (ttl <= 0), don't add it
    if (expiry !== Infinity && this.#isExpired(expiry)) {
      return this;
    }

    // Handle capacity
    if (this.#cache.size >= this.#capacity) {
      // 1. Try to purge expired entries to make room
      this.#purgeExpired();

      // 2. If still at capacity, evict the Least Recently Used (first item in Map)
      if (this.#cache.size >= this.#capacity) {
        const firstKey = this.#cache.keys().next().value;
        this.#cache.delete(firstKey);
      }
    }

    this.#cache.set(key, { value, expiry });
    return this;
  }

  /**
   * Returns the value and makes the entry most recently used.
   * Returns undefined if absent or expired.
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
   * Does not affect recency.
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
   * Removes the entry. Returns true if something was removed.
   */
  delete(key) {
    return this.#cache.delete(key);
  }

  /**
   * Returns an array of live keys ordered from most recently used to least recently used.
   */
  keys() {
    this.#purgeExpired();
    // Map iterator is oldest -> newest. We reverse it for newest -> oldest.
    return Array.from(this.#cache.keys()).reverse();
  }
}
