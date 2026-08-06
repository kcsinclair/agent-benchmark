export class LruTtlCache {
  /**
   * @param {{capacity: number, defaultTtlMs?: number, now?: () => number}} options
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> {value, expiry}
  }

  /**
   * Insert or replace a key.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs]
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const now = this._now();
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : now + ttl;

    // If already expired, remove any existing entry and do not store
    if (expiry <= now) {
      this._map.delete(key);
      return this;
    }

    // Remove existing to update recency
    if (this._map.has(key)) {
      this._map.delete(key);
    }

    this._map.set(key, { value, expiry });

    // Evict if over capacity
    this._evictIfNeeded();
    return this;
  }

  /**
   * Get value for key, updating recency.
   * @param {*} key
   * @returns {*|undefined}
   */
  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;
    const now = this._now();
    if (entry.expiry !== Infinity && now >= entry.expiry) {
      this._map.delete(key);
      return undefined;
    }
    // Update recency: move to end
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  /**
   * Check existence without affecting recency.
   * @param {*} key
   * @returns {boolean}
   */
  has(key) {
    const entry = this._map.get(key);
    if (!entry) return false;
    const now = this._now();
    if (entry.expiry !== Infinity && now >= entry.expiry) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Delete key.
   * @param {*} key
   * @returns {boolean}
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live entries.
   */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Array of live keys from most recent to least.
   * @returns {Array}
   */
  keys() {
    this._purgeExpired();
    return [...this._map.keys()].reverse();
  }

  /* Internal helpers */

  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._map.entries()) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  _evictIfNeeded() {
    // First purge expired entries
    this._purgeExpired();
    while (this._map.size > this._capacity) {
      // Evict least recently used: first key in Map
      const lruKey = this._map.keys().next().value;
      this._map.delete(lruKey);
    }
  }
}
