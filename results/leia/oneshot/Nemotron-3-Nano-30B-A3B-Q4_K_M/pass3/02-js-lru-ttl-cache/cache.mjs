// cache.mjs
export class LruTtlCache {
  /**
   * @param {Object} opts
   * @param {number} opts.capacity - Must be >= 1
   * @param {number} [opts.defaultTtlMs=Infinity] - Default TTL in ms
   * @param {() => number} [opts.now=() => Date.now()] - Clock function returning ms
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
  _getEntry(key) {
    return this._map.get(key);
  }

  /** @param {any} key */
  _removeEntry(key) {
    this._map.delete(key);
  }

  /** @param {any} key */
  _setEntry(key, entry) {
    this._map.set(key, entry);
  }

  /** @returns {number} current time in ms */
  _now() {
    return this._now();
  }

  /** @param {Entry} entry */
  _isExpired(entry) {
    if (entry.ttlMs === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  /** @param {Entry} entry */
  _touch(entry) {
    // make most recently used: move to end of Map (already there if accessed via get/set)
    // but ensure recency when accessed via has/delete etc.
    // Since Map preserves insertion order, we need to re‑insert to update recency.
    const val = this._map.get(entry.key);
    if (val !== entry) {
      this._map.delete(entry.key);
      this._setEntry(entry.key, entry);
    }
  }

  /** @param {any} key */
  set(key, value, ttlMs) {
    const now = this._now();
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === 0 || ttl < 0 ? now : now + ttl; // already expired if ttl <= 0

    const entry = {
      key,
      value,
      expiry,
      ttlMs,
      // store original key to allow SameValueZero comparison for deletion
      // but Map already uses SameValueZero, so no extra work needed
    };

    // If key exists, replace value and expiry, then mark as most recent
    if (this._map.has(key)) {
      this._removeEntry(key);
    }

    this._setEntry(key, entry);
    // Ensure recency: re‑insert updates insertion order
    this._touch(entry);

    // Eviction loop: first purge expired, then evict LRU until within capacity
    while (this.size > this._capacity) {
      // Find the least recently used entry (first inserted that is still present)
      // Since we never reorder on get, the first key in the map is the LRU.
      // But we might have moved entries via _touch, so the LRU is the first key
      // that has not been touched recently.
      // To get LRU we can iterate over map keys; worst-case O(n) but amortized O(1)
      // because we only evict when over capacity and each entry is removed once.
      const firstKey = this._map.keys().next().value;
      const firstEntry = this._map.get(firstKey);
      if (this._isExpired(firstEntry)) {
        this._removeEntry(firstKey);
      } else {
        this._removeEntry(firstKey);
        break;
      }
    }

    return this;
  }

  /** @param {any} key */
  get(key) {
    const entry = this._getEntry(key);
    if (!entry) return undefined;
    if (this._isExpired(entry)) {
      this._removeEntry(key);
      return undefined;
    }
    // Mark as most recently used
    this._touch(entry);
    return entry.value;
  }

  /** @param {any} key */
  has(key) {
    const entry = this._getEntry(key);
    if (!entry) return false;
    if (this._isExpired(entry)) {
      this._removeEntry(key);
      return false;
    }
    // Do not affect recency
    return true;
  }

  /** @param {any} key */
  delete(key) {
    return this._map.delete(key);
  }

  /** @returns {number} number of live entries */
  get size() {
    let count = 0;
    for (const entry of this._map.values()) {
      if (!this._isExpired(entry)) count++;
    }
    return count;
  }

  /** @returns {any[]} array of live keys from most recent to least */
  keys() {
    const live = [];
    // Map iteration yields keys in insertion order (oldest → newest)
    // We need most recent first, so we collect then reverse.
    for (const k of this._map.keys()) {
      const entry = this._map.get(k);
      if (!this._isExpired(entry)) live.push(k);
    }
    // Reverse to get newest (most recent) first
    live.reverse();
    return live;
  }
}
