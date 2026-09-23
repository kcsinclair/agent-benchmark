// cache.mjs
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map preserves insertion order; we delete+set to mark MRU.
    // Values are stored as { value, expiry }.
    this._map = new Map();
  }

  _isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this._now() >= expiry;
  }

  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs === undefined ? this._defaultTtlMs : ttlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;

    if (this._map.has(key)) {
      // Delete and re-insert to move to MRU position.
      this._map.delete(key);
    }
    this._map.set(key, { value, expiry });

    // Purge expired entries if over capacity.
    if (this._map.size > this._capacity) {
      this._purgeExpired();
      while (this._map.size > this._capacity) {
        // Evict LRU (first entry).
        const oldestKey = this._map.keys().next().value;
        this._map.delete(oldestKey);
      }
    }
    return this;
  }

  get(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return undefined;
    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this._map.delete(key);
      return undefined;
    }
    // Move to MRU.
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;
    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this._map.delete(key);
  }

  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  keys() {
    this._purgeExpired();
    return Array.from(this._map.keys());
  }
}
