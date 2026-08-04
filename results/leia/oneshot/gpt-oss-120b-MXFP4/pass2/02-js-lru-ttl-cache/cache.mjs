/**
 * LRU Cache with per‑entry TTL.
 *
 * The implementation uses a single `Map` where the insertion order represents
 * recency: the most‑recently used entry is always at the *end* of the map.
 * Accesses (`get`, `set`) delete the entry and re‑insert it, moving it to the
 * end in O(1) amortised time.
 *
 * All time calculations use the injected `now` function – never `Date.now()`.
 *
 * @example
 *   import { LruTtlCache } from './cache.mjs';
 *   const cache = new LruTtlCache({ capacity: 2, defaultTtlMs: 1000 });
 *   cache.set('a', 1);
 *   cache.get('a'); // 1
 */

export class LruTtlCache {
  /**
   * @param {Object} opts
   * @param {number} opts.capacity          – maximum number of live entries (≥1)
   * @param {number} [opts.defaultTtlMs=Infinity] – default TTL in ms
   * @param {()=>number} [opts.now=()=>Date.now()] – clock function
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    /** @type {Map<any,{value:any,expiry:number}>} */
    this._map = new Map(); // key → {value, expiry}
  }

  /** --------------------------------------------------------------------
   *  Internal helpers
   * ------------------------------------------------------------------- */

  /** @private */
  _nowMs() {
    return this._now();
  }

  /** @private */
  _isExpired(entry) {
    const now = this._nowMs();
    return entry.expiry !== Infinity && now >= entry.expiry;
  }

  /** @private
   *  Remove every expired entry from the map.
   */
  _purgeExpired() {
    const now = this._nowMs();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  /** @private
   *  Ensure the cache respects its capacity:
   *   1. Remove all expired entries.
   *   2. If still too large, evict the least‑recently used entries.
   */
  _evictIfNeeded() {
    this._purgeExpired();

    while (this._map.size > this._capacity) {
      // LRU entry is the first one in insertion order.
      const lruKey = this._map.keys().next().value;
      this._map.delete(lruKey);
    }
  }

  /** --------------------------------------------------------------------
   *  Public API
   * ------------------------------------------------------------------- */

  /**
   * Insert or replace a value.
   *
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs] – overrides the default TTL for this entry
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;

    // ttl ≤ 0 means the entry is already expired – just ensure it is absent.
    if (ttl <= 0) {
      this._map.delete(key);
      return this;
    }

    const expiry = ttl === Infinity ? Infinity : this._nowMs() + ttl;

    // Remove existing entry first so that the new one becomes most‑recent.
    if (this._map.has(key)) this._map.delete(key);
    this._map.set(key, { value, expiry });

    this._evictIfNeeded();
    return this;
  }

  /**
   * Retrieve a value and mark the entry as most‑recently used.
   *
   * @param {*} key
   * @returns {*} the stored value, or `undefined` if missing/expired
   */
  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }

    // Move to the end (most recent)
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  /**
   * Test for presence without affecting recency.
   *
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
   *
   * @param {*} key
   * @returns {boolean} `true` if something was removed
   */
  delete(key) {
    return this._map.delete(key);
  }

  /** @type {number} */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Return live keys ordered from most‑recently used to least‑recently used.
   *
   * @returns {Array<any>}
   */
  keys() {
    this._purgeExpired();
    // Map iterates from oldest → newest; we need newest → oldest.
    return Array.from(this._map.keys()).reverse();
  }
}
