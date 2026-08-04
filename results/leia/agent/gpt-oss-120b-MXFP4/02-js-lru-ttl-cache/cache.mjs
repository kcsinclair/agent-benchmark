// cache.mjs
// LRU Cache with TTL implementation
// Exported class LruTtlCache as per specification.

export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity - maximum number of live entries (>=1)
   * @param {number} [options.defaultTtlMs=Infinity] - default TTL in ms
   * @param {function} [options.now=()=>Date.now()] - clock function returning ms
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // internal map: key -> { value, expiry }
    // Insertion order reflects recency: newest (most recently used) at the end.
    this._map = new Map();
  }

  // Internal helper: determine if an entry is expired.
  _isExpired(entry) {
    const now = this._now();
    return entry.expiry !== Infinity && now >= entry.expiry;
  }

  // Remove all expired entries from the cache.
  _purgeExpired() {
    for (const [key, entry] of this._map) {
      if (this._isExpired(entry)) {
        this._map.delete(key);
      }
    }
  }

  // Move an existing entry to the most-recent position.
  _moveToRecent(key, entry) {
    // Deleting and re‑setting moves the key to the end of insertion order.
    this._map.delete(key);
    this._map.set(key, entry);
  }

  /**
   * Insert or replace a value.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs] - optional TTL for this entry
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;
    const entry = { value, expiry };

    // If key already exists, delete it first so that the new entry becomes most recent.
    if (this._map.has(key)) {
      this._map.delete(key);
    }
    this._map.set(key, entry);

    // Remove any entries that are now expired (including possibly the one we just added).
    this._purgeExpired();

    // Evict least‑recently‑used entries if we exceed capacity.
    while (this._map.size > this._capacity) {
      const lruKey = this._map.keys().next().value; // first inserted = least recent
      this._map.delete(lruKey);
    }
    return this;
  }

  /**
   * Retrieve a value and mark it as most recently used.
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
    // Refresh recency.
    this._moveToRecent(key, entry);
    return entry.value;
  }

  /**
   * Check presence without affecting recency.
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
   * Delete an entry.
   * @param {*} key
   * @returns {boolean} true if something was removed
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live (non‑expired) entries.
   */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Array of live keys ordered from most recently used to least recently used.
   * @returns {Array}
   */
  keys() {
    this._purgeExpired();
    const keys = Array.from(this._map.keys());
    // Map iteration order is oldest → newest, so reverse for MRU → LRU.
    return keys.reverse();
  }
}
