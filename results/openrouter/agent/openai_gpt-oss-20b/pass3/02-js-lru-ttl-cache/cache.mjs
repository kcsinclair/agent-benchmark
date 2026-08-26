export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  _isExpired(entry) {
    return entry.expiry !== Infinity && this.now() >= entry.expiry;
  }

  _purgeExpired() {
    const now = this.now();
    for (const [key, entry] of this._map.entries()) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.now() + ttl;
    if (this._map.has(key)) {
      this._map.delete(key);
    }
    this._map.set(key, { value, expiry });

    if (this._map.size > this.capacity) {
      // Evict expired entries first
      this._purgeExpired();
      // If still over capacity, evict least recently used entries
      while (this._map.size > this.capacity) {
        const firstKey = this._map.keys().next().value;
        this._map.delete(firstKey);
      }
    }
    return this;
  }

  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    // Move to most recently used (end of map)
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._map.get(key);
    if (!entry) return false;
    if (this._isExpired(entry)) {
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
    // Map order is oldest to newest; reverse for most recent first
    return Array.from(this._map.keys()).reverse();
  }
}
