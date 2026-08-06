// cache.mjs
// LRU cache with per‑entry TTL
// Node.js ES module – no external dependencies

export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity   – maximum number of live entries (≥ 1)
   * @param {number} [options.defaultTtlMs=Infinity] – default TTL in ms
   * @param {() => number} [options.now=() => Date.now()] – injected clock
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    // Map keeps insertion order – we use it to track recency.
    // key → { value, expiry }
    this.map = new Map();
  }

  /* ------------------------------------------------------------------ */
  /* Internal helpers */

  /** @private */
  _isExpired(entry) {
    // Infinity never expires
    return entry.expiry !== Infinity && this.now() >= entry.expiry;
  }

  /** @private
   * Remove all expired entries from the cache.
   * Complexity: O(n) – acceptable for the limited use cases
   */
  _purgeExpired() {
    for (const [key, entry] of this.map.entries()) {
      if (this._isExpired(entry)) {
        this.map.delete(key);
      }
    }
  }

  /* ------------------------------------------------------------------ */
  /* Public API */

  /**
   * Insert or replace an entry.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs] – TTL in ms for this entry
   * @returns {LruTtlCache} – for chaining
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs === undefined ? this.defaultTtlMs : ttlMs;
    const expiry = ttl === Infinity ? Infinity : this.now() + ttl;

    const existing = this.map.get(key);
    if (existing !== undefined && !this._isExpired(existing)) {
      // Live key – just replace and move to end
      this.map.delete(key);
    } else {
      // New key or expired key – may need eviction
      this._purgeExpired(); // remove all expired entries first
      if (this.map.size >= this.capacity) {
        // Still over capacity → evict LRU (first key in Map)
        const lruKey = this.map.keys().next().value;
        this.map.delete(lruKey);
      }
    }

    this.map.set(key, { value, expiry });
    return this;
  }

  /**
   * Retrieve a value and mark the entry as most‑recently used.
   * @param {*} key
   * @returns {*} value or undefined if missing/expired
   */
  get(key) {
    const entry = this.map.get(key);
    if (entry === undefined) return undefined;

    if (this._isExpired(entry)) {
      this.map.delete(key);
      return undefined;
    }

    // Move to end (most recent)
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  /**
   * Check existence of a live entry (does not affect recency).
   * @param {*} key
   * @returns {boolean}
   */
  has(key) {
    const entry = this.map.get(key);
    if (entry === undefined) return false;
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Remove an entry.
   * @param {*} key
   * @returns {boolean} – true if something was removed
   */
  delete(key) {
    return this.map.delete(key);
  }

  /**
   * Number of live (non‑expired) entries.
   * @returns {number}
   */
  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  /**
   * Array of live keys ordered from most recent to least recent.
   * @returns {Array}
   */
  keys() {
    this._purgeExpired();
    return Array.from(this.map.keys());
  }
}
