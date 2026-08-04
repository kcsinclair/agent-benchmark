// LRU Cache with per‑entry TTL.
// Implementation uses a single Map where the *insertion order* represents
// recency (the newest entry is at the end).  Moving an entry to the end is
// done by deleting it and re‑inserting it, which is O(1) amortised.
//
// All time calculations use the injected `now` function, never `Date.now()`.

export class LruTtlCache {
  /**
   * @param {Object} opts
   * @param {number} opts.capacity          – integer ≥ 1
   * @param {number} [opts.defaultTtlMs=Infinity] – default TTL in ms
   * @param {function} [opts.now=()=>Date.now()] – clock function returning ms
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map: key → { value, expiry }
    // `expiry` is a number (ms since epoch) or Infinity (never expires)
    this._map = new Map();
  }

  /* ---------- internal helpers ---------- */

  // true if the entry is expired at the current moment
  _isExpired(entry) {
    const now = this._now();
    return entry.expiry !== Infinity && now >= entry.expiry;
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

  // Ensure the cache respects its capacity:
  //   1. Remove expired entries.
  //   2. If still too large, evict the least‑recently‑used (oldest) entry.
  _ensureCapacity() {
    this._purgeExpired();
    while (this._map.size > this._capacity) {
      // LRU is the first entry in insertion order.
      const lruKey = this._map.keys().next().value;
      this._map.delete(lruKey);
    }
  }

  /* ---------- public API ---------- */

  /**
   * Insert or replace a value.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs] – overrides default TTL for this entry
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const now = this._now();

    // ttl ≤ 0 means the entry is already expired – just ensure it is absent.
    if (ttl <= 0) {
      this._map.delete(key);
      return this;
    }

    const expiry = ttl === Infinity ? Infinity : now + ttl;

    // Delete first so that re‑insertion moves the key to the “most recent” spot.
    if (this._map.has(key)) this._map.delete(key);
    this._map.set(key, { value, expiry });

    this._ensureCapacity();
    return this;
  }

  /**
   * Retrieve a value and mark it as most‑recently used.
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

    // Move to most‑recent position.
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

  /** Number of live (non‑expired) entries. */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Array of live keys ordered from most‑recently used to least‑recently used.
   * @returns {Array}
   */
  keys() {
    const now = this._now();
    const rawKeys = Array.from(this._map.keys()); // insertion order (old → new)
    const result = [];

    // Walk backwards (new → old) to produce MRU → LRU.
    for (let i = rawKeys.length - 1; i >= 0; i--) {
      const k = rawKeys[i];
      const entry = this._map.get(k);
      if (!entry) continue; // should not happen, but be safe

      if (entry.expiry !== Infinity && now >= entry.expiry) {
        // Expired – clean it up.
        this._map.delete(k);
        continue;
      }
      result.push(k);
    }
    return result;
  }
}
