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

  _purgeExpired() {
    // Since we need to maintain O(1) for most operations, 
    // we don't iterate the whole map unless necessary.
    // However, the 'size' getter and 'keys' method require a clean state.
    for (const [key, entry] of this._cache.entries()) {
      if (this._isExpired(entry)) {
        this._cache.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    const expiry = ttlMs !== undefined 
      ? this._now() + ttlMs 
      : this._now() + this._defaultTtlMs;

    this._cache.set(key, { value, expiry });

    if (this._cache.size > this._capacity) {
      // First, try to evict any expired entries to make room
      for (const [k, entry] of this._cache.entries()) {
        if (this._isExpired(entry)) {
          this._cache.delete(k);
          if (this._cache.size <= this._capacity) break;
        }
      }

      // If still over capacity, evict the LRU (the first entry in the Map)
      if (this._cache.size > this._capacity) {
        const firstKey = this._cache.keys().next().value;
        this._cache.delete(firstKey);
      }
    }

    return this;
  }

  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry)) {
      this._cache.delete(key);
      return undefined;
    }

    // Refresh recency: delete and re-insert
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

  get size() {
    this._purgeExpired();
    return this._cache.size;
  }

  keys() {
    this._purgeExpired();
    // Map keys are in insertion order (LRU is first, MRU is last).
    // Requirement: MRU to LRU.
    return Array.from(this._cache.keys()).reverse();
  }
}
