/**
 * LRU cache where each entry also has a time-to-live.
 *
 * - Recency and storage are backed by a single `Map`, which preserves
 *   insertion order. To mark an entry as most-recently-used we delete and
 *   re-insert it; the least-recently-used entry is therefore always the first
 *   key returned by `map.keys()`.
 * - All time arithmetic goes through the injected `now()` clock so the cache
 *   can be driven by a fake clock in tests.
 */
export class LruTtlCache {
  /**
   * @param {object} options
   * @param {number} options.capacity     Maximum number of live entries (integer >= 1).
   * @param {number} [options.defaultTtlMs=Infinity] TTL applied when `set` omits one.
   * @param {() => number} [options.now=() => Date.now()] Injected clock in ms.
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    /** @private */
    this._capacity = capacity;
    /** @private */
    this._defaultTtlMs = defaultTtlMs;
    /** @private */
    this._now = now;
    /**
     * key -> { value, expiry }
     * Insertion order encodes recency: first = LRU, last = MRU.
     * @private
     */
    this._map = new Map();
  }

  /**
   * True when the expiry instant has been reached. `Infinity` never expires.
   * @private
   */
  _isExpired(expiry, now) {
    return expiry !== Infinity && now >= expiry;
  }

  /**
   * Remove an entry if its TTL has passed.
   * @returns {boolean} whether the entry was expired and removed.
   * @private
   */
  _purgeIfExpired(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;
    if (this._isExpired(entry.expiry, this._now())) {
      this._map.delete(key);
      return true;
    }
    return false;
  }

  /** Purge every expired entry. @private */
  _purgeAll() {
    const now = this._now();
    for (const [key, entry] of this._map) {
      if (this._isExpired(entry.expiry, now)) {
        this._map.delete(key);
      }
    }
  }

  /** Move an existing key to the most-recently-used position. @private */
  _touch(key) {
    const entry = this._map.get(key);
    this._map.delete(key);
    this._map.set(key, entry);
  }

  /**
   * Insert or replace an entry.
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs === undefined ? this._defaultTtlMs : ttlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;

    // Replacing an existing key: drop it first so it re-enters as MRU.
    this._map.delete(key);
    this._map.set(key, { value, expiry });

    if (this._map.size > this._capacity) {
      // Evict expired entries first...
      this._purgeAll();
      // ...then fall back to evicting the LRU entry while over capacity.
      while (this._map.size > this._capacity) {
        const oldest = this._map.keys().next().value;
        this._map.delete(oldest);
      }
    }

    return this;
  }

  /**
   * Get and touch a live entry, or `undefined` if absent/expired.
   */
  get(key) {
    if (this._purgeIfExpired(key)) return undefined;
    const entry = this._map.get(key);
    if (entry === undefined) return undefined;
    this._touch(key);
    return entry.value;
  }

  /**
   * Whether a live entry exists. Does not affect recency.
   */
  has(key) {
    if (this._purgeIfExpired(key)) return false;
    return this._map.has(key);
  }

  /**
   * Remove an entry.
   * @returns {boolean} whether an entry was removed.
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live entries, purging any that have expired.
   */
  get size() {
    this._purgeAll();
    return this._map.size;
  }

  /**
   * Live keys from most recently used to least recently used.
   */
  keys() {
    this._purgeAll();
    return [...this._map.keys()].reverse();
  }
}

export default LruTtlCache;
