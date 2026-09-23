/**
 * LRU cache with per-entry TTL support.
 *
 * Recency is tracked using a Map's insertion order:
 *   - The first entry is the least recently used (LRU).
 *   - The last entry is the most recently used (MRU).
 * Touching an entry (get / set) deletes and re-inserts it to move it to the
 * end, keeping all operations O(1) amortized.
 */
export class LruTtlCache {
  /**
   * @param {object} options
   * @param {number} options.capacity Maximum number of live entries. Integer >= 1.
   * @param {number} [options.defaultTtlMs=Infinity] Default TTL for entries.
   * @param {() => number} [options.now=() => Date.now()] Injected clock.
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // key -> { value, expiry }  (insertion order == recency order)
    this._map = new Map();
  }

  /** @returns {boolean} whether the entry for `key` is present but expired. */
  _isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this._now() >= expiry;
  }

  /** Remove `key` if present and expired. @returns {boolean} true if removed. */
  _purgeIfExpired(key) {
    const entry = this._map.get(key);
    if (entry !== undefined && this._isExpired(entry.expiry)) {
      this._map.delete(key);
      return true;
    }
    return false;
  }

  /** Remove all expired entries. */
  _purgeAllExpired() {
    // Snapshot the clock so a single logical operation uses one time value.
    const t = this._now();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && t >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  /** Move an existing key to the MRU position (no-op if absent). */
  _touch(key) {
    const entry = this._map.get(key);
    if (entry !== undefined) {
      this._map.delete(key);
      this._map.set(key, entry);
    }
  }

  /**
   * Insert or replace an entry.
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs === undefined ? this._defaultTtlMs : ttlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;

    // Replace: remove old position first so re-insert moves to MRU.
    if (this._map.has(key)) {
      this._map.delete(key);
    }

    this._map.set(key, { value, expiry });

    // Handle capacity: evict expired first, then LRU.
    if (this._map.size > this._capacity) {
      this._purgeAllExpired();
    }
    while (this._map.size > this._capacity) {
      // Evict the least recently used (first inserted) live entry.
      const lruKey = this._map.keys().next().value;
      this._map.delete(lruKey);
    }

    return this;
  }

  /**
   * Get a value, marking the entry as most recently used.
   * @returns {*} the value, or undefined if absent/expired.
   */
  get(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return undefined;
    if (this._isExpired(entry.expiry)) {
      this._map.delete(key);
      return undefined;
    }
    this._touch(key);
    return entry.value;
  }

  /**
   * Check presence without affecting recency.
   * @returns {boolean}
   */
  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;
    if (this._isExpired(entry.expiry)) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Delete an entry.
   * @returns {boolean} true if something was removed.
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live (non-expired) entries. Purges expired entries.
   * @returns {number}
   */
  get size() {
    this._purgeAllExpired();
    return this._map.size;
  }

  /**
   * Live keys from most recently used to least recently used.
   * @returns {Array<*>}
   */
  keys() {
    this._purgeAllExpired();
    const result = [];
    // Map iterates oldest -> newest; reverse to get MRU first.
    for (const key of this._map.keys()) {
      result.push(key);
    }
    return result.reverse();
  }
}

export default LruTtlCache;
