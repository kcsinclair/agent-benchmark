// LRU Cache with per‑entry TTL
// ---------------------------------------------------------------
// Exported class LruTtlCache implements the API described in the
// problem statement.  It uses a native Map to keep insertion order,
// treating the *newest* entry (the one most recently set / accessed) as
// the most‑recently‑used.  When an entry is touched we delete it and
// re‑insert it, which moves it to the end of the Map (O(1) amortised).
// ---------------------------------------------------------------

export class LruTtlCache {
  /**
   * @param {Object} opts
   * @param {number} opts.capacity          – integer ≥ 1
   * @param {number} [opts.defaultTtlMs=Infinity] – default TTL in ms
   * @param {function} [opts.now=()=>Date.now()] – clock function
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    /** @type {Map<any,{value:any,expiry:number}>} */
    this._map = new Map(); // insertion order = LRU order (oldest → newest)
  }

  // -----------------------------------------------------------------
  // internal helpers
  // -----------------------------------------------------------------
  _nowMs() {
    return this._now();
  }

  /** @param {{expiry:number}} entry */
  _isExpired(entry) {
    const now = this._nowMs();
    return entry.expiry !== Infinity && now >= entry.expiry;
  }

  /** Remove all expired entries (oldest → newest). */
  _purgeExpired() {
    for (const [k, entry] of this._map) {
      if (this._isExpired(entry)) this._map.delete(k);
    }
  }

  /** Ensure the cache respects its capacity after an insertion. */
  _ensureCapacity() {
    // 1️⃣  Evict expired entries first.
    this._purgeExpired();

    // 2️⃣  If still over capacity, evict the least‑recently‑used entry,
    //     i.e. the *oldest* entry in the Map.
    while (this._map.size > this._capacity) {
      const oldestKey = this._map.keys().next().value;
      this._map.delete(oldestKey);
    }
  }

  // -----------------------------------------------------------------
  // public API
  // -----------------------------------------------------------------
  /**
   * Insert or replace a value.
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs] – overrides default TTL for this entry
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const now = this._nowMs();

    // Compute expiry. Infinity stays Infinity.
    const expiry = ttl === Infinity ? Infinity : now + ttl;

    // If the entry would already be expired, simply ensure it is not stored.
    if (expiry !== Infinity && expiry <= now) {
      this._map.delete(key);
      return this;
    }

    // Remove existing entry first so that re‑insertion moves it to the end.
    if (this._map.has(key)) this._map.delete(key);

    this._map.set(key, { value, expiry });

    // Possibly evict entries to respect capacity.
    this._ensureCapacity();

    return this;
  }

  /**
   * Retrieve a value, promoting it to most‑recently‑used.
   * @param {*} key
   * @returns {*} value or undefined if missing / expired
   */
  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }

    // Promote to most‑recently‑used.
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
   * Array of live keys ordered from most‑recently‑used to least‑recently‑used.
   * @returns {Array<any>}
   */
  keys() {
    this._purgeExpired();
    // Map iteration order = oldest → newest.
    // Reverse to get newest → oldest.
    return Array.from(this._map.keys()).reverse();
  }
}
