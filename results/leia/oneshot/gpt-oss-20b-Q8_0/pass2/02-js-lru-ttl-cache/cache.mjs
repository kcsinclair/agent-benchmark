// cache.mjs
// LRU cache with per‑entry TTL
// Node.js 20+ ES module

export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity - maximum number of live entries (≥ 1)
   * @param {number} [options.defaultTtlMs=Infinity] - default TTL in ms
   * @param {() => number} [options.now=Date.now] - injected clock function
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key → { value, expiry }
  }

  /* ------------------------------------------------------------------ */
  /*  Helpers                                                            */
  /* ------------------------------------------------------------------ */

  /** @private */
  _isExpired(entry) {
    return entry.expiry !== Infinity && this._now() >= entry.expiry;
  }

  /** @private */
  _purgeExpired() {
    for (const [k, v] of this._map) {
      if (this._isExpired(v)) {
        this._map.delete(k);
      }
    }
  }

  /* ------------------------------------------------------------------ */
  /*  Public API                                                         */
  /* ------------------------------------------------------------------ */

  /**
   * Insert or replace a key/value pair.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs] - TTL in ms for this entry
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const expiry = this._now() + (ttlMs ?? this._defaultTtlMs);
    const entry = { value, expiry };

    // Move to the end (most‑recently used)
    if (this._map.has(key)) this._map.delete(key);
    this._map.set(key, entry);

    // Evict if we exceed capacity
    while (this._map.size > this._capacity) {
      const firstKey = this._map.keys().next().value;
      const firstEntry = this._map.get(firstKey);
      this._map.delete(firstKey);
      // If the removed entry was expired we already reduced size,
      // otherwise we removed one LRU entry and are now within capacity.
      if (this._map.size <= this._capacity) break;
    }

    return this;
  }

  /**
   * Retrieve a value by key.
   * @param {*} key
   * @returns {*} value or undefined if missing/expired
   */
  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }

    // Move to the end (most‑recently used)
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  /**
   * Check if a key exists and is not expired.
   * Does NOT affect recency.
   * @param {*} key
   * @returns {boolean}
   */
  has(key) {
    const entry = this._map.get(key);
    if (!entry) return false;

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Delete a key.
   * @param {*} key
   * @returns {boolean} true if something was removed
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live (non‑expired) entries.
   * Purges expired entries before returning the count.
   */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Array of live keys ordered from most‑recently used to least‑recently used.
   */
  keys() {
    this._purgeExpired();
    return Array.from(this._map.keys()).reverse();
  }
}
