export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._cache = new Map();
  }

  _isExpired(entry) {
    return entry.expiry !== Infinity && this._now() >= entry.expiry;
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;
    const entry = { value, expiry };

    if (this._cache.has(key)) {
      this._cache.delete(key);
    } else {
      // Evict expired entries first to make room
      this._purgeExpired();
      
      if (this._cache.size >= this._capacity) {
        // Evict the least recently used (the first key in the Map)
        const lruKey = this._cache.keys().next().value;
        this._cache.delete(lruKey);
      }
    }

    this._cache.set(key, entry);
    return this;
  }

  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry)) {
      this._cache.delete(key);
      return undefined;
    }

    // Move to most recently used
    this._cache.delete(key);
    this._cache.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._cache.get(key);
    if (!entry) return false;

    if (this._isExpired(entry)) {
      this._cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this._cache.delete(key);
  }

  _purgeExpired() {
    for (const [key, entry] of this._cache.entries()) {
      if (this._isExpired(entry)) {
        this._cache.delete(key);
      }
    }
  }

  get size() {
    this._purgeExpired();
    return this._cache.size;
  }

  keys() {
    this._purgeExpired();
    // Map keys are in insertion order (LRU first, MRU last)
    // Return MRU to LRU
    return Array.from(this._cache.keys()).reverse();
  }
}
