export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity - maximum number of live entries (>=1)
   * @param {number} [options.defaultTtlMs=Infinity] - default TTL in ms
   * @param {() => number} [options.now=() => Date.now()] - clock function
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (typeof capacity !== 'number' || !Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  /**
   * Insert or replace a key/value pair.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs]
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;
    const entry = { value, expiry };

    // Purge expired entries before adding
    this._purgeExpired();

    if (this._map.has(key)) {
      this._map.delete(key);
    }
    this._map.set(key, entry);

    // Purge any entry that might have expired immediately
    this._purgeExpired();

    // Evict if over capacity
    while (this._map.size > this._capacity) {
      const oldestKey = this._map.keys().next().value;
      this._map.delete(oldestKey);
    }
    return this;
  }

  /**
   * Retrieve a value by key.
   * @param {*} key
   * @returns {*} value or undefined
   */
  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    // Move to most-recently-used position
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  /**
   * Check if a key exists and is not expired.
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
   * @returns {boolean} true if key existed
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live (non-expired) entries.
   * @returns {number}
   */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Array of live keys from most-recently-used to least-recently-used.
   * @returns {Array}
   */
  keys() {
    this._purgeExpired();
    return Array.from(this._map.keys()).reverse();
  }

  /* Internal helpers */
  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  _purgeExpired() {
    for (const [k, v] of this._map) {
      if (this._isExpired(v)) {
        this._map.delete(k);
      }
    }
  }
}
