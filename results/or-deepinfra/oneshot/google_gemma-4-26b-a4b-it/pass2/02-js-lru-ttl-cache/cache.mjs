/**
 * LruTtlCache implementation
 * 
 * Uses a Map to maintain insertion order, which in JavaScript 
 * provides O(1) access and allows us to simulate an LRU 
 * by re-inserting keys to move them to the "most recent" position.
 */
export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity - Maximum number of live entries.
   * @param {number} [options.defaultTtlMs=Infinity] - Default TTL in ms.
   * @param {Function} [options.now=() => Date.now()] - Clock function.
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("Capacity must be an integer >= 1");
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map stores key -> { value, expiry }
    // Map maintains insertion order: first item is LRU, last is MRU.
    this._cache = new Map();
  }

  /**
   * Internal helper to purge expired entries.
   * Since we don't have a priority queue for time, we must iterate 
   * or rely on lazy deletion. The requirements specify that size, 
   * get, has, and set must handle expiration.
   */
  _purgeExpired() {
    const currentTime = this._now();
    for (const [key, entry] of this._cache.entries()) {
      if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
        this._cache.delete(key);
      }
    }
  }

  /**
   * @returns {number} Number of live (non-expired) entries.
   */
  get size() {
    this._purgeExpired();
    return this._cache.size;
  }

  /**
   * @param {*} key
   * @returns {*} The value or undefined.
   */
  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this._cache.delete(key);
      return undefined;
    }

    // Refresh recency: delete and re-insert
    this._cache.delete(key);
    this._cache.set(key, entry);
    return entry.value;
  }

  /**
   * @param {*} key
   * @returns {boolean}
   */
  has(key) {
    const entry = this._cache.get(key);
    if (!entry) return false;

    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this._cache.delete(key);
      return false;
    }
    return true;
  }

  /**
   * @param {*} key
   * @returns {boolean} True if entry existed and was removed.
   */
  delete(key) {
    return this._cache.delete(key);
  }

  /**
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs]
   * @returns {LruTtlCache}
   */
  set(key, value, ttlMs) {
    const currentTime = this._now();
    const effectiveTtl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : currentTime + effectiveTtl;

    // If key exists, remove it first to update recency/value
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    // Check capacity constraints
    // 1. Try to make room by purging expired entries
    this._purgeExpired();

    // 2. If still at capacity, evict the LRU (the first item in Map)
    if (this._cache.size >= this._capacity) {
      const lruKey = this._cache.keys().next().value;
      this._cache.delete(lruKey);
    }

    // Note: If ttlMs <= 0, the entry is technically expired immediately.
    // However, the requirement says "insert or replace". 
    // If it's expired, it will be cleaned up on the next access/size call.
    this._cache.set(key, { value, expiry });
    return this;
  }

  /**
   * @returns {Array<*>} Keys from MRU to LRU.
   */
  keys() {
    this._purgeExpired();
    // Map.keys() returns in insertion order (LRU -> MRU).
    // We need MRU -> LRU.
    return Array.from(this._cache.keys()).reverse();
  }
}
