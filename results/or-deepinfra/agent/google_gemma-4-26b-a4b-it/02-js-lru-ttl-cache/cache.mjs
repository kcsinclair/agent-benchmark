export class LruTtlCache {
  /**
   * @param {{ capacity: number, defaultTtlMs?: number, now?: () => number }} options
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    
    // Map maintains insertion order.
    // We use it to track recency: 
    // - Most recently used is at the end of the Map.
    // - Least recently used is at the beginning of the Map.
    this._cache = new Map();
  }

  /**
   * @returns {number} number of live (non-expired) entries
   */
  get size() {
    this._purgeExpired();
    return this._cache.size;
  }

  /**
   * @returns {Array} array of live keys ordered from most recently used to least recently used
   */
  keys() {
    this._purgeExpired();
    // Map iterator is in insertion order (LRU to MRU).
    // We need MRU to LRU, so we reverse the array.
    return Array.from(this._cache.keys()).reverse();
  }

  /**
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs]
   * @returns {LruTtlCache}
   */
  set(key, value, ttlMs) {
    const expiry = this._now() + (ttlMs ?? this._defaultTtlMs);

    // If key exists, remove it first to update recency/order
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    // Check capacity
    if (this._cache.size >= this._capacity) {
      // 1. Try to purge expired entries first
      this._purgeExpired();
      
      // 2. If still at capacity, evict the LRU (the first item in Map)
      if (this._cache.size >= this._capacity) {
        const firstKey = this._cache.keys().next().value;
        this._cache.delete(firstKey);
      }
    }

    this._cache.set(key, { value, expiry });
    return this;
  }

  /**
   * @param {*} key
   * @returns {*}
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
   * @param {*} key
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
   * @param {*} key
   * @returns {boolean}
   */
  delete(key) {
    return this._cache.delete(key);
  }

  /**
   * Internal helper to purge all expired entries.
   */
  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._cache.entries()) {
      if (this._isExpired(entry.expiry, now)) {
        this._cache.delete(key);
      }
    }
  }

  _isExpired(expiry, now = this._now()) {
    if (expiry === Infinity) return false;
    return now >= expiry;
  }
}
