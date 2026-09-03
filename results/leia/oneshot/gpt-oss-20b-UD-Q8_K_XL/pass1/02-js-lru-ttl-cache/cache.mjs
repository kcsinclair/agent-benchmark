// cache.mjs
// LRU cache with per‑entry TTL
// Node 20+ ES‑module

export class LruTtlCache {
  /**
   * @param {Object} options
   * @param {number} options.capacity   – maximum number of live entries (≥ 1)
   * @param {number} [options.defaultTtlMs=Infinity] – default TTL in ms
   * @param {() => number} [options.now=Date.now] – injected clock
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
  /*  Helpers                                                             */
  /* ------------------------------------------------------------------ */

  /** @private */
  _isExpired(entry) {
    const expiry = entry.expiry;
    return expiry !== Infinity && this.now() >= expiry;
  }

  /** @private */
  _purgeExpired() {
    for (const [key, entry] of this.map) {
      if (this._isExpired(entry)) {
        this.map.delete(key);
      }
    }
  }

  /* ------------------------------------------------------------------ */
  /*  Public API                                                          */
  /* ------------------------------------------------------------------ */

  /**
   * Insert or replace a key/value pair.
   * @param {any} key
   * @param {any} value
   * @param {number} [ttlMs] – TTL in ms; if omitted, defaultTtlMs is used
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.now() + ttl;

    const exists = this.map.has(key);

    if (exists) {
      // Replace – delete first to move to the end
      this.map.delete(key);
    } else {
      // New key – may need eviction
      if (this.map.size >= this.capacity) {
        // 1️⃣ Evict expired entries first
        for (const [k, e] of this.map) {
          if (this._isExpired(e)) {
            this.map.delete(k);
            if (this.map.size < this.capacity) break;
          }
        }
        // 2️⃣ If still over capacity, evict LRU entries
        while (this.map.size >= this.capacity) {
          const lruKey = this.map.keys().next().value;
          this.map.delete(lruKey);
        }
      }
    }

    this.map.set(key, { value, expiry });
    return this;
  }

  /**
   * Retrieve a value and mark the entry as most‑recently used.
   * @param {any} key
   * @returns {any | undefined}
   */
  get(key) {
    const entry = this.map.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry)) {
      this.map.delete(key);
      return undefined;
    }

    // Move to the end (most recent)
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
    const entry = this.map.get(key);
    if (!entry) return false;

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
    this._purgeExpired();
    return Array.from(this.map.keys()).reverse();
  }
}
