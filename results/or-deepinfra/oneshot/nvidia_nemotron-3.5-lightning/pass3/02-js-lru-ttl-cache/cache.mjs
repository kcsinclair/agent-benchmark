// cache.mjs

export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("capacity must be an integer >= 1");
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  set(key, value, ttlMs) {
    const now = this._now();
    const expiry = ttlMs !== undefined ? now + ttlMs : this._defaultTtlMs;

    // If key exists, update value and expiry, move to front (most recent)
    if (this._map.has(key)) {
      const entry = this._map.get(key);
      entry.value = value;
      entry.expiry = expiry;
      this._map.delete(key);
      this._map.set(key, entry);
      return this;
    }

    // Insert new entry
    const entry = { value, expiry };
    this._map.set(key, entry);

    // Evict if over capacity
    this._trim();

    return this;
  }

  get(key) {
    if (!this._map.has(key)) return undefined;

    const entry = this._map.get(key);
    const now = this._now();

    // Expired?
    if (entry.expiry !== Infinity && now >= entry.expiry) {
      this._map.delete(key);
      return undefined;
    }

    // Move to front (most recently used)
    const value = entry.value;
    this._map.delete(key);
    this._map.set(key, entry);
    return value;
  }

  has(key) {
    if (!this._map.has(key)) return false;

    const entry = this._map.get(key);
    const now = this._now();

    // Expired? remove and return false
    if (entry.expiry !== Infinity && now >= entry.expiry) {
      this._map.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this._map.delete(key);
  }

  get size() {
    const now = this._now();
    let count = 0;
    for (const entry of this._map.values()) {
      if (entry.expiry === Infinity || now < entry.expiry) {
        count++;
      }
    }
    // Purge expired entries
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
    return count;
  }

  keys() {
    // Purge expired entries first
    this._purgeExpired();

    // Return live keys in MRU to LRU order (Map insertion order)
    const liveKeys = [];
    for (const [key] of this._map) {
      const entry = this._map.get(key);
      if (entry.expiry === Infinity || this._now() < entry.expiry) {
        liveKeys.push(key);
      }
    }
    return liveKeys;
  }

  // Internal: remove all expired entries
  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  // Internal: ensure size <= capacity by evicting expired then LRU
  _trim() {
    // First, purge all expired entries
    this._purgeExpired();

    // If still over capacity, evict the least recently used (last in Map order)
    while (this._map.size > this._capacity) {
      const lastKey = this._map.keys().next().value;
      this._map.delete(lastKey);
    }
  }
}
