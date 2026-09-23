/**
 * LruTtlCache — an LRU cache where every entry also has a time-to-live.
 *
 * Recency is tracked with a Map's insertion order:
 *   - the Map's first key is the least recently used
 *   - the Map's last key is the most recently used
 * "Touching" an entry (get / set) deletes and re-inserts it to move it to the end.
 */

const NEVER = Infinity;

export class LruTtlCache {
  /**
   * @param {object} options
   * @param {number} options.capacity        Max number of live entries (integer >= 1).
   * @param {number} [options.defaultTtlMs]  TTL used when set() omits ttlMs.
   * @param {() => number} [options.now]     Injected clock returning ms.
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (
      typeof capacity !== 'number' ||
      !Number.isInteger(capacity) ||
      capacity < 1
    ) {
      throw new RangeError(
        `capacity must be an integer >= 1, received ${String(capacity)}`
      );
    }

    /** @type {Map<any, { value: any, expiry: number }>} */
    this._map = new Map();
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
  }

  /**
   * True if the entry has expired at the current time.
   * Infinity expiry never expires. Expiry instant itself counts as expired.
   * @private
   */
  _isExpired(entry) {
    if (entry.expiry === NEVER) return false;
    return this._now() >= entry.expiry;
  }

  /**
   * Remove a single key if present. Returns true if removed.
   * @private
   */
  _deleteKey(key) {
    return this._map.delete(key);
  }

  /**
   * Remove all expired entries. O(n) worst case, but stale entries are only
   * scanned when capacity or the live-size getter demands it.
   * @private
   */
  _purgeExpired() {
    // Fast path: nothing can be expired if no finite expiry exists.
    for (const [key, entry] of this._map) {
      if (this._isExpired(entry)) {
        this._map.delete(key);
      }
    }
  }

  /**
   * Move an existing key to the most-recently-used position.
   * Assumes the entry is live and already present.
   * @private
   */
  _touch(key, entry) {
    this._map.delete(key);
    this._map.set(key, entry);
  }

  /**
   * Insert or replace an entry.
   * @param {any} key
   * @param {any} value
   * @param {number} [ttlMs]
   * @returns {this}
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs === undefined ? this._defaultTtlMs : ttlMs;
    const expiry = ttl === NEVER ? NEVER : this._now() + ttl;

    // Remove any existing entry first so re-insertion lands at the MRU end.
    if (this._map.has(key)) {
      this._map.delete(key);
    }

    this._map.set(key, { value, expiry });

    // Enforce capacity: purge expired entries first, then evict by LRU.
    if (this._map.size > this._capacity) {
      this._purgeExpired();
      while (this._map.size > this._capacity) {
        // First key in Map iteration order is the least recently used.
        const oldest = this._map.keys().next().value;
        this._map.delete(oldest);
      }
    }

    return this;
  }

  /**
   * Return the value for a key (making it MRU), or undefined if absent/expired.
   * @param {any} key
   * @returns {any}
   */
  get(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return undefined;

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }

    this._touch(key, entry);
    return entry.value;
  }

  /**
   * True if the key is present and not expired. Does not affect recency.
   * Removes the entry if discovered to be expired.
   * @param {any} key
   * @returns {boolean}
   */
  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Remove a key. Returns true if something was removed.
   * @param {any} key
   * @returns {boolean}
   */
  delete(key) {
    return this._map.delete(key);
  }

  /**
   * Number of live (non-expired) entries. Purges expired entries.
   * @returns {number}
   */
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  /**
   * Live keys ordered from most recently used to least recently used.
   * @returns {any[]}
   */
  keys() {
    this._purgeExpired();
    const out = [];
    for (const key of this._map.keys()) out.push(key);
    // Map order is LRU -> MRU; reverse for MRU -> LRU.
    out.reverse();
    return out;
  }
}
