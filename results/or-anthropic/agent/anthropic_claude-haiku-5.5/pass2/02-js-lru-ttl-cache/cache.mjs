export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map insertion order: first = least recently used, last = most recently used.
    this._map = new Map();
  }

  _expiryFor(ttlMs) {
    const ttl = ttlMs === undefined || ttlMs === null ? this._defaultTtlMs : ttlMs;
    if (ttl === Infinity) return Infinity;
    return this._now() + ttl;
  }

  _isExpired(entry, t = this._now()) {
    return entry.expiresAt !== Infinity && t >= entry.expiresAt;
  }

  _purgeExpired() {
    const t = this._now();
    for (const [k, entry] of this._map) {
      if (this._isExpired(entry, t)) this._map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const expiresAt = this._expiryFor(ttlMs);
    if (this._map.has(key)) this._map.delete(key);
    this._map.set(key, { value, expiresAt });
    if (this._map.size > this._capacity) {
      this._purgeExpired();
      while (this._map.size > this._capacity) {
        const oldestKey = this._map.keys().next().value;
        this._map.delete(oldestKey);
      }
    }
    return this;
  }

  get(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return undefined;
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    // Move to most recently used.
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;
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
    return [...this._map.keys()].reverse();
  }
}
