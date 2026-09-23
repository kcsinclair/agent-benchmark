// cache.mjs
export class LruTtlCache {
  /**
   * @param {Object} opts
   * @param {number} opts.capacity - Must be >= 1
   * @param {number} [opts.defaultTtlMs=Infinity] - Default TTL in ms
   * @param {() => number} [opts.now=Date.now] - Clock function returning ms
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;

    /** @type {Map<any, Entry>} */
    this._map = new Map();
  }

  /** @param {any} key */
  _set(key, value, ttlMs) {
    const now = this._now();
    const expiry = ttlMs === Infinity ? Infinity : now + ttlMs;
    if (expiry <= now) return; // already expired

    const entry = { value, expiry };
    this._map.set(key, entry);
    this._touch(key);
    this._evictIfNeeded();
    return this;
  }

  /** @param {any} key */
  _get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;
    if (entry.expiry !== Infinity && entry.expiry <= this._now()) {
      this._map.delete(key);
      return undefined;
    }
    this._touch(key);
    return entry.value;
  }

  /** @param {any} key */
  _has(key) {
    const entry = this._map.get(key);
    if (!entry) return false;
    if (entry.expiry !== Infinity && entry.expiry <= this._now()) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  /** @param {any} key */
  _delete(key) {
    return this._map.delete(key);
  }

  /** @param {any} key */
  _touch(key) {
    // Move accessed/updated entry to the end (most‑recently‑used)
    const entry = this._map.get(key);
    if (entry) {
      this._map.delete(key);
      this._map.set(key, entry);
    }
  }

  /** @param {any} key */
  _evictIfNeeded() {
    // 1️⃣ Evict expired entries first
    for (const [k, e] of this._map) {
      if (e.expiry !== Infinity && e.expiry <= this._now()) {
        this._map.delete(k);
      }
    }

    // 2️⃣ If still over capacity, evict LRU (first entry)
    while (this._map.size > this._capacity) {
      const firstKey = this._map.keys().next().value;
      this._map.delete(firstKey);
    }
  }

  /** @returns {number} */
  get size() {
    // Purge expired entries before counting
    this._evictIfNeeded();
    return this._map.size;
  }

  /** @returns {Array<any>} */
  keys() {
    this._evictIfNeeded();
    return Array.from(this._map.keys()).reverse(); // most recent at end → reverse for MRU→LRU
  }
}
