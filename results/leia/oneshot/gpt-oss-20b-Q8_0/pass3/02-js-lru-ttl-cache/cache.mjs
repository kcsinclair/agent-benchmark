// cache.mjs
// LRU cache with TTL – ES‑module implementation

export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity   – maximum number of live entries (≥ 1)
   * @param {number} [options.defaultTtlMs=Infinity] – default TTL in ms
   * @param {function(): number} [options.now=Date.now] – clock function
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    /** @type {Map<any, {value: any, expiry: number}>} */
    this.map = new Map();
  }

  /* ------------------------------------------------------------------ */
  /* Internal helpers                                                   */
  /* ------------------------------------------------------------------ */

  /** @private */
  _isExpired(entry) {
    return entry.expiry !== Infinity && this.now() >= entry.expiry;
  }

  /** @private */
  _purgeExpired() {
    const now = this.now();
    for (const [key, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
      }
    }
  }

  /* ------------------------------------------------------------------ */
  /* Public API                                                         */
  /* ------------------------------------------------------------------ */

  /**
   * Insert or replace a key/value pair.
   * @param {any} key
   * @param {any} value
   * @param {number} [ttlMs] – TTL in ms for this entry
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const expiry = this.now() + (ttlMs ?? this.defaultTtlMs);

    // Replace existing entry (also moves it to the end)
    if (this.map.has(key)) this.map.delete(key);
    this.map.set(key, { value, expiry });

    // Evict expired entries first
    this._purgeExpired();

    // If still over capacity, evict LRU entries
    while (this.map.size > this.capacity) {
      const lruKey = this.map.keys().next().value; // first key = LRU
      this.map.delete(lruKey);
    }

    return this;
  }

  /**
   * Retrieve a value by key.
   * @param {any} key
   * @returns {any | undefined}
   */
  get(key) {
    if (!this.map.has(key)) return undefined;

    const entry = this.map.get(key);
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return undefined;
    }

    // Move to the end (most‑recently used)
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  /**
   * Check if a key exists and is not expired.
   * Does NOT affect recency.
   * @param {any} key
   * @returns {boolean}
   */
  has(key) {
    if (!this.map.has(key)) return false;

    const entry = this.map.get(key);
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  /**
   * Delete a key.
   * @param {any} key
   * @returns {boolean} – true if something was removed
   */
  delete(key) {
    return this.map.delete(key);
  }

  /**
   * Number of live (non‑expired) entries.
   * Purges expired entries before returning the count.
   */
  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  /**
   * Array of live keys ordered from most‑recently used to least‑recently used.
   */
  keys() {
    const keys = [];
    const now = this.now();

    for (const [key, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
      } else {
        keys.push(key);
      }
    }

    // Map order is LRU → MRU, so reverse to get MRU → LRU
    return keys.reverse();
  }
}
