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

  set(key, value, ttlMs) {
    // If key exists, remove it first to update position (recency)
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    const expiry = this._now() + (ttlMs ?? this._defaultTtlMs);
    this._cache.set(key, { value, expiry });

    // Evict if over capacity
    if (this._cache.size > this._capacity) {
      this._evict();
    }

    return this;
  }

  get(key) {
    if (!this._cache.has(key)) return undefined;

    const entry = this._cache.get(key);
    if (this._isExpired(entry)) {
      this._cache.delete(key);
      return undefined;
    }

    // Update recency: move to end of Map
    this._cache.delete(key);
    this._cache.set(key, entry);
    return entry.value;
  }

  has(key) {
    if (!this._cache.has(key)) return false;

    const entry = this._cache.get(key);
    if (this._isExpired(entry)) {
      this._cache.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this._cache.delete(key);
  }

  get size() {
    this._purgeExpired();
    return this._cache.size;
  }

  keys() {
    this._purgeExpired();
    // Map keys are in insertion order (LRU is at the start, MRU at the end)
    // Requirement: MRU to LRU
    return Array.from(this._cache.keys()).reverse();
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._cache.entries()) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._cache.delete(key);
      }
    }
  }

  _evict() {
    // 1. Try to evict expired entries first
    this._purgeExpired();

    // 2. If still over capacity, evict the least recently used (first entry in Map)
    if (this._cache.size > this._capacity) {
      const firstKey = this._cache.keys().next().value;
      this._cache.delete(firstKey);
    }
  }
}
