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
   * Internal helper to check if an entry is expired.
   * @param {number} expiry 
   * @returns {boolean}
   */
  #isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this.#now() >= expiry;
  }

  /**
   * Internal helper to purge all expired entries currently in the map.
   * This is called during size access and capacity management.
   */
  #purgeExpired() {
    for (const [key, entry] of this.#cache.entries()) {
      if (this.#isExpired(entry.expiry)) {
        this.#cache.delete(key);
      }
    }
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

  set(key, value, ttlMs) {
    // If key exists, remove it first to update recency/value
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    const ttl = ttlMs !== undefined ? ttlMs : this.#defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.#now() + ttl;

    // If the new entry is already expired (ttl <= 0), don't add it
    // unless we want to allow "dead" entries. Per requirements:
    // "ttlMs of 0 or negative means the entry is already expired."
    // We only add it if it's valid, or we add it and it gets purged.
    // To strictly follow "insert or replace", we add it.
    this.#cache.set(key, { value, expiry });

    // Handle capacity
    if (this.#cache.size > this.#capacity) {
      // 1. Try to purge expired entries first to free space
      this.#purgeExpired();

      // 2. If still over capacity, evict the LRU (the first item in Map iterator)
      if (this.#cache.size > this.#capacity) {
        const firstKey = this.#cache.keys().next().value;
        this.#cache.delete(firstKey);
      }
    }

    return this;
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
    this.#purgeExpired();
    return this.#cache.size;
  }

  keys() {
    this.#purgeExpired();
    // Map.keys() returns in insertion order. 
    // Since we re-insert on 'get', the first is MRU, last is LRU.
    // Requirement: "ordered from most recently used to least recently used".
    return Array.from(this.#cache.keys()).reverse();
  }
}
