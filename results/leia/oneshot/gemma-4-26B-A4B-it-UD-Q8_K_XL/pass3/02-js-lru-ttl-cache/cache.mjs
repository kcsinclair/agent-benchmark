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
   * Since we cannot guarantee all expired entries are at the end of the Map,
   * we must iterate. However, the requirement for O(1) amortized applies 
   * to the primary API.
   */
  #purgeExpired() {
    const currentTime = this.#now();
    for (const [key, entry] of this.#cache.entries()) {
      if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
        this.#cache.delete(key);
      }
    }
  }

  /**
   * Returns the number of live (non-expired) entries.
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
    const currentTime = this.#now();
    const effectiveTtl = ttlMs !== undefined ? ttlMs : this.#defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : currentTime + effectiveTtl;

    // If key exists, remove it first to update recency via re-insertion
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    // If at capacity, try to make room
    if (this.#cache.size >= this.#capacity) {
      this.#purgeExpired();
      
      // If still at capacity after purging expired, evict LRU (the first item in Map)
      if (this.#cache.size >= this.#capacity) {
        const firstKey = this.#cache.keys().next().value;
        this.#cache.delete(firstKey);
      }
    }

    // If the new entry is already expired (ttl <= 0), we don't actually store it
    // unless it's Infinity. But per requirements: "ttlMs of 0 or negative means 
    // the entry is already expired." We follow standard cache behavior: 
    // if it's expired immediately, it's effectively not "set" or immediately removed.
    if (expiry !== Infinity && currentTime >= expiry) {
      return this;
    }

    this.#cache.set(key, { value, expiry });
    return this;
  }

  /**
   * Returns value and updates recency. Returns undefined if absent or expired.
   */
  get(key) {
    const entry = this.#cache.get(key);
    if (!entry) return undefined;

    const currentTime = this.#now();
    if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
      this.#cache.delete(key);
      return undefined;
    }

    // Refresh recency: delete and re-insert
    this.#cache.delete(key);
    this.#cache.set(key, entry);
    return entry.value;
  }

  /**
   * Returns true if present and not expired. Does not affect recency.
   */
  has(key) {
    const entry = this.#cache.get(key);
    if (!entry) return false;

    const currentTime = this.#now();
    if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
      this.#cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Removes the entry.
   */
  delete(key) {
    return this.#cache.delete(key);
  }

  /**
   * Returns array of live keys from MRU to LRU.
   */
  keys() {
    this.#purgeExpired();
    // Map.keys() returns in insertion order (LRU to MRU). 
    // We need MRU to LRU, so we reverse it.
    return Array.from(this.#cache.keys()).reverse();
  }
}
