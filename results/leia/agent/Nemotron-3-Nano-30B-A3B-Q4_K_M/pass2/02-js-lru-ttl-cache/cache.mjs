export class LruTtlCache {
  /**
   * @param {Object} opts
   * @param {number} opts.capacity - integer >= 1
   * @param {number} [opts.defaultTtlMs=Infinity]
   * @param {function(): number} [opts.now] - returns ms; defaults to Date.now()
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    /** @type {Map<any, {value: any, expiry: number|Infinity}>} */
    this.map = new Map();
  }

  /** @private */
  _purgeExpired() {
    const now = this.now();
    for (const [key, { expiry }] of this.map) {
      if (expiry !== Infinity && now >= expiry) {
        this.map.delete(key);
      }
    }
  }

  /** @returns {LruTtlCache} */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.now() + ttl;

    // If key exists, remove old entry to update recency later
    if (this.map.has(key)) {
      this.map.delete(key);
    }

    this.map.set(key, { value, expiry });

    // Enforce capacity: first purge expired, then evict LRU if still over capacity
    while (this.map.size > this.capacity) {
      this._purgeExpired();
      if (this.map.size <= this.capacity) break;
      const lruKey = this.map.keys().next().value; // oldest entry
      this.map.delete(lruKey);
    }

    return this;
  }

  /** @returns {any|undefined} */
  get(key) {
    if (!this.map.has(key)) return undefined;

    const entry = this.map.get(key);
    // Check expiration
    if (entry.expiry !== Infinity && this.now() >= entry.expiry) {
      this.map.delete(key);
      return undefined;
    }

    // Move to most recent
    this.map.delete(key);
    this.map.set(key, entry); // re‑insert places it at the end (most recent)
    return entry.value;
  }

  /** @returns {boolean} */
  has(key) {
    if (!this.map.has(key)) return false;
    const entry = this.map.get(key);
    if (entry.expiry !== Infinity && this.now() >= entry.expiry) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  /** @returns {boolean} */
  delete(key) {
    return this.map.delete(key);
  }

  /** @returns {number} */
  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  /** @returns {any[]} */
  keys() {
    this._purgeExpired();
    // Map iteration order: oldest → newest; reverse to get newest → oldest
    return Array.from(this.map.keys()).reverse();
  }
}
