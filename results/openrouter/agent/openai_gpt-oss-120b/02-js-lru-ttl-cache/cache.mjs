// cache.mjs
// LRU Cache with TTL implementation
// Exported class LruTtlCache as per problem statement.

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
    // Map preserves insertion order. We treat the *end* of the map as the most
    // recently used entry. When an entry is accessed or set we delete it and
    // re‑insert, moving it to the end.
    this._map = new Map(); // key -> { value, expiry }
  }

  // Internal helper: determine if an entry is expired.
  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  // Remove all expired entries from the map.
  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  // Ensure the cache respects capacity after a mutation.
  _ensureCapacity() {
    // First drop any expired entries.
    this._purgeExpired();
    // Then evict least‑recently‑used entries while over capacity.
    while (this._map.size > this._capacity) {
      const lruKey = this._map.keys().next().value; // first (oldest) key
      this._map.delete(lruKey);
    }
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
    // If ttl is non‑positive, the entry is already expired – ensure it is not stored.
    if (ttl <= 0) {
      this._map.delete(key);
      return this;
    }
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;
    // Delete existing entry so that re‑insertion moves it to the end (most recent).
    if (this._map.has(key)) this._map.delete(key);
    this._map.set(key, { value, expiry });
    this._ensureCapacity();
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
    // Move to most recent position.
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  /**
   * Test presence without affecting recency.
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
   * Remove an entry.
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
    // Ensure we only return live keys.
    this._purgeExpired();
    // Map iteration order is LRU → MRU, so reverse it.
    return Array.from(this._map.keys()).reverse();
  }
}
