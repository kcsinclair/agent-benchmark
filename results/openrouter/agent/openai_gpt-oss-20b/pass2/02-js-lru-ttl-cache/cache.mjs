export class LruTtlCache {
  /**
   * @param {{ capacity: number, defaultTtlMs?: number, now?: () => number }} options
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  /**
   * @private
   * @param {{ value: any, expiry: number }} entry
   * @returns {boolean}
   */
  _isExpired(entry) {
    return entry.expiry !== Infinity && this._now() >= entry.expiry;
  }

  /**
   * Evict expired entries from the front (least‑recently used) until none remain.
   * @private
   */
  _purgeExpiredFromFront() {
    while (this._map.size > 0) {
      const first = this._map.entries().next().value;
      if (!first) break;
      const [key, entry] = first;
      if (this._isExpired(entry)) {
        this._map.delete(key);
      } else {
        break;
      }
    }
  }

  /**
   * Insert or replace a key.
   * @param {any} key
   * @param {any} value
   * @param {number} [ttlMs]
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const now = this._now();
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : now + ttl;

    // If ttl is 0 or negative, the entry is already expired.
    if (ttl <= 0) {
      this._map.delete(key);
      return this;
    }

    // Remove existing key to move it to the end later.
    if (this._map.has(key)) {
      this._map.delete(key);
    }

    // Ensure capacity: evict expired entries from front first.
    if (this._map.size >= this._capacity) {
      this._purgeExpiredFromFront();
      if (this._map.size >= this._capacity) {
        // Evict least‑recently used (first entry)
        const lruKey = this._map.keys().next().value;
        this._map.delete(lruKey);
      }
    }

    this._map.set(key, { value, expiry });
    return this;
  }

  /**
   * Retrieve a value and mark it as most recently used.
   * @param {any} key
   * @returns {any|undefined}
   */
  get(key) {
    if (!this._map.has(key)) return undefined;
    const entry = this._map.get(key);
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    // Move to end to mark as most recently used.
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  /**
   * Check existence without affecting recency.
   * @param {any} key
   * @returns {boolean}
   */
  has(key) {
    if (!this._map.has(key)) return false;
    const entry = this._map.get(key);
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Delete a key.
   * @param {any} key
   * @returns {boolean}
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live (non‑expired) entries.
   * @returns {number}
   */
  get size() {
    // Purge all expired entries.
    for (const [key, entry] of this._map.entries()) {
      if (this._isExpired(entry)) {
        this._map.delete(key);
      }
    }
    return this._map.size;
  }

  /**
   * Array of live keys from most recently used to least.
   * @returns {any[]}
   */
  keys() {
    const keys = [];
    for (const [key, entry] of this._map.entries()) {
      if (this._isExpired(entry)) {
        this._map.delete(key);
      } else {
        keys.push(key);
      }
    }
    return keys.reverse();
  }
}
