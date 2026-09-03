// cache.mjs
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  /* ---------- internal helpers ---------- */

  _isExpired(entry) {
    return entry.expiry !== Infinity && this._now() >= entry.expiry;
  }

  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }

  _moveToEnd(key, entry) {
    this._map.delete(key);
    this._map.set(key, entry);
  }

  _evictLRU() {
    const lruKey = this._map.keys().next().value;
    if (lruKey !== undefined) {
      this._map.delete(lruKey);
    }
  }

  /* ---------- public API ---------- */

  set(key, value, ttlMs) {
    const now = this._now();
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = now + ttl;

    // If ttl <= 0, the entry is already expired – do not store it.
    if (ttl <= 0) {
      if (this._map.has(key)) this._map.delete(key);
      return this;
    }

    // Remove expired entries first
    this._purgeExpired();

    const existing = this._map.get(key);
    if (existing && !this._isExpired(existing)) {
      // Update value and expiry, move to most recent
      existing.value = value;
      existing.expiry = expiry;
      this._moveToEnd(key, existing);
      return this;
    }

    // If key existed but was expired, delete it
    if (existing) this._map.delete(key);

    // Evict if over capacity
    if (this._map.size >= this._capacity) {
      this._evictLRU();
    }

    // Insert new entry
    this._map.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this._map.get(key);
    if (!entry) return undefined;
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    this._moveToEnd(key, entry);
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
    return [...this._map.keys()].reverse(); // most recent first
  }
}
