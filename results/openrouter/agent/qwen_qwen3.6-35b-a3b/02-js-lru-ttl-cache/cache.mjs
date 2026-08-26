export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map stores: key -> { value, expiry }
    // Map insertion order = LRU order (oldest first, newest last)
    this._map = new Map();
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  _purgeExpired() {
    for (const [key, entry] of this._map) {
      if (this._isExpired(entry)) {
        this._map.delete(key);
      }
    }
  }

  _evictIfNeeded() {
    // First, purge any expired entries
    this._purgeExpired();

    // If still over capacity, evict LRU (first in Map iteration order)
    while (this._map.size > this._capacity) {
      // Get the first key (least recently used)
      const firstKey = this._map.keys().next().value;
      this._map.delete(firstKey);
    }
  }

  set(key, value, ttlMs) {
    const expiry = ttlMs !== undefined
      ? this._now() + ttlMs
      : (this._defaultTtlMs === Infinity ? Infinity : this._now() + this._defaultTtlMs);

    // Evict before inserting to make room if needed
    this._evictIfNeeded();

    // Insert/update the entry
    this._map.set(key, { value, expiry });

    return this;
  }

  get(key) {
    // Check if key exists
    if (!this._map.has(key)) {
      return undefined;
    }

    const entry = this._map.get(key);

    // Check if expired
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }

    // Move to most recently used by re-inserting
    this._map.delete(key);
    this._map.set(key, entry);

    return entry.value;
  }

  has(key) {
    if (!this._map.has(key)) {
      return false;
    }

    const entry = this._map.get(key);

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    if (!this._map.has(key)) {
      return false;
    }

    const entry = this._map.get(key);

    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }

    this._map.delete(key);
    return true;
  }

  get size() {
    // Purge expired and return count of live entries
    this._purgeExpired();
    return this._map.size;
  }

  keys() {
    // Purge expired first
    this._purgeExpired();

    // Return keys in LRU order (most recently used first)
    // Map iteration is oldest first, so we reverse
    const keyArray = Array.from(this._map.keys());
    return keyArray.reverse();
  }
}
