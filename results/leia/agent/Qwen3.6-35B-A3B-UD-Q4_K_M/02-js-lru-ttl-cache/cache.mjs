export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map preserves insertion order; we'll use it as our LRU store.
    // Entries: { value, expiry }
    this._store = new Map();
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  _purgeExpired() {
    for (const [key, entry] of this._store) {
      if (this._isExpired(entry)) {
        this._store.delete(key);
      }
    }
  }

  _evictExpiredFirst() {
    // Remove expired entries (any order is fine for eviction)
    for (const [key, entry] of this._store) {
      if (this._isExpired(entry)) {
        this._store.delete(key);
      }
    }
  }

  _evictLru() {
    // The first entry in the Map is the least recently used
    // (since we always move accessed/updated keys to the end)
    if (this._store.size > 0) {
      const firstKey = this._store.keys().next().value;
      this._store.delete(firstKey);
    }
  }

  set(key, value, ttlMs) {
    const expiry = ttlMs === undefined
      ? (this._defaultTtlMs === Infinity ? Infinity : this._now() + this._defaultTtlMs)
      : (ttlMs === Infinity ? Infinity : this._now() + ttlMs);

    // If the entry is already expired (ttlMs <= 0 and not Infinity),
    // we still store it but it will be treated as expired immediately.
    // Actually, per spec: ttlMs of 0 or negative means the entry is already expired.
    // We should store it but it will be purged on next access.
    // However, to keep size accurate, let's just store it and let the
    // expiration logic handle it.

    // If key already exists, delete it first so it moves to the end (MRU)
    if (this._store.has(key)) {
      this._store.delete(key);
    }

    // If adding this entry would exceed capacity, evict
    if (this._store.size >= this._capacity) {
      this._evictExpiredFirst();
      if (this._store.size >= this._capacity) {
        this._evictLru();
      }
    }

    this._store.set(key, { value, expiry });
    return this;
  }

  get(key) {
    if (!this._store.has(key)) {
      return undefined;
    }
    const entry = this._store.get(key);
    if (this._isExpired(entry)) {
      this._store.delete(key);
      return undefined;
    }
    // Move to end (MRU)
    this._store.delete(key);
    this._store.set(key, entry);
    return entry.value;
  }

  has(key) {
    if (!this._store.has(key)) {
      return false;
    }
    const entry = this._store.get(key);
    if (this._isExpired(entry)) {
      this._store.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    if (this._store.has(key)) {
      this._store.delete(key);
      return true;
    }
    return false;
  }

  get size() {
    // Purge expired and return count
    this._purgeExpired();
    return this._store.size;
  }

  keys() {
    // Purge expired first
    this._purgeExpired();
    // Map iteration order is insertion order, which is LRU order
    // (MRU is at the end). We want MRU first.
    const result = [];
    for (const [key] of this._store) {
      result.push(key);
    }
    return result.reverse();
  }
}
