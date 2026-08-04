export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    // Map preserves insertion order; we move entries to end on access.
    // Each value is { value, expiry }
    this.map = new Map();
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this.now() >= entry.expiry;
  }

  _purgeExpired() {
    const now = this.now();
    for (const [key, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
      }
    }
  }

  _evictLru() {
    // Map iteration order is insertion order (with moves).
    // The first entry is the least recently used.
    if (this.map.size > 0) {
      const key = this.map.keys().next().value;
      this.map.delete(key);
    }
  }

  set(key, value, ttlMs) {
    const effectiveTtl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : this.now() + effectiveTtl;

    if (this.map.has(key)) {
      // Update existing: move to end (most recently used)
      this.map.delete(key);
    } else {
      // New entry: check capacity
      // First, purge expired entries
      this._purgeExpired();
      // If still over capacity, evict LRU
      while (this.map.size >= this.capacity) {
        this._evictLru();
      }
    }

    this.map.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this.map.get(key);
    if (entry === undefined) {
      return undefined;
    }
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return undefined;
    }
    // Move to end (most recently used)
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.map.get(key);
    if (entry === undefined) {
      return false;
    }
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.map.delete(key);
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    // Map iteration order is from least recently used to most recently used.
    // We need most recently used to least recently used.
    const allKeys = [...this.map.keys()];
    return allKeys.reverse();
  }
}
