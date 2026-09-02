/**
 * LruTtlCache implements a Least Recently Used cache with Time-To-Live (TTL) support.
 * It leverages the fact that JavaScript Map preserves insertion order.
 */
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer >= 1');
    }

    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    
    // Map stores: key => { value, expiry }
    this._cache = new Map();
  }

  /**
   * Internal helper to check if an entry is expired.
   */
  _isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this._now() >= expiry;
  }

  /**
   * Inserts or updates a key-value pair.
   * @returns {LruTtlCache}
   */
  set(key, value, ttlMs) {
    // If key exists, remove it first to update recency (move to end of Map)
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;

    this._cache.set(key, { value, expiry });

    // Eviction logic:
    // 1. First, purge any expired entries to make room.
    // 2. If still over capacity, remove the oldest (first) entry.
    if (this._cache.size > this._capacity) {
      this._purgeExpired();
    }

    if (this._cache.size > this._capacity) {
      const oldestKey = this._cache.keys().next().value;
      this._cache.delete(oldestKey);
    }

    return this;
  }

  /**
   * Retrieves a value and updates its recency.
   * @returns {any|undefined}
   */
  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry.expiry)) {
      this._cache.delete(key);
      return undefined;
    }

    // Update recency: delete and re-insert
    this._cache.delete(key);
    this._cache.set(key, entry);
    return entry.value;
  }

  /**
   * Checks if a key exists and is not expired.
   * Does not affect recency.
   * @returns {boolean}
   */
  has(key) {
    const entry = this._cache.get(key);
    if (!entry) return false;

    if (this._isExpired(entry.expiry)) {
      this._cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Removes a key from the cache.
   * @returns {boolean}
   */
  delete(key) {
    return this._cache.delete(key);
  }

  /**
   * Returns the number of non-expired entries.
   * Purges expired entries during the count.
   */
  get size() {
    this._purgeExpired();
    return this._cache.size;
  }

  /**
   * Returns live keys ordered from most recently used to least recently used.
   * @returns {Array}
   */
  keys() {
    this._purgeExpired();
    // Map keys are in insertion order (LRU is at the start, MRU at the end).
    // We need MRU to LRU, so we reverse the array.
    return Array.from(this._cache.keys()).reverse();
  }

  /**
   * Iterates through the map and removes all expired entries.
   */
  _purgeExpired() {
    for (const [key, entry] of this._cache.entries()) {
      if (this._isExpired(entry.expiry)) {
        this._cache.delete(key);
      }
    }
  }
}
