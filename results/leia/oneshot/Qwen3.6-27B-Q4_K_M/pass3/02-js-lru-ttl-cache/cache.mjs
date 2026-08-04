export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    // Map preserves insertion order; we move entries to end on access to track recency.
    // Each value is { value, expiry }
    this.map = new Map();
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) {
      return false;
    }
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
    // Evict expired entries first
    this._purgeExpired();
    // If still over capacity, evict LRU (first entry in Map)
    while (this.map.size > this.capacity) {
      const firstKey = this.map.keys().next().value;
      this.map.delete(firstKey);
    }
  }

  set(key, value, ttlMs) {
    const effectiveTtl = ttlMs ?? this.defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : this.now() + effectiveTtl;
    
    // If key exists, update it and move to end (most recently used)
    if (this.map.has(key)) {
      this.map.set(key, { value, expiry });
      this.map.delete(key); // Remove from current position
      this.map.set(key, { value, expiry }); // Re-insert at end
    } else {
      // New entry
      this.map.set(key, { value, expiry });
      // Check capacity
      if (this.map.size > this.capacity) {
        this._evictLru();
      }
    }
    return this;
  }

  get(key) {
    const entry = this.map.get(key);
    if (!entry) {
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
    if (!entry) {
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
    // Purge expired entries and return count of live entries
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    // Purge expired entries first
    this._purgeExpired();
    // Map iteration order is insertion order, which we maintain as recency order
    // (most recently used at the end). We need most recently used first.
    const allKeys = [...this.map.keys()];
    return allKeys.reverse();
  }
}
