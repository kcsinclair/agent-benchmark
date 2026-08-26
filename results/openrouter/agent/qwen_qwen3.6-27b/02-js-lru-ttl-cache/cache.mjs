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

  _evictExpired() {
    const now = this.now();
    for (const [key, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
      }
    }
  }

  _evictLru() {
    // The first entry in the Map is the least recently used
    if (this.map.size > 0) {
      const key = this.map.keys().next().value;
      this.map.delete(key);
    }
  }

  _touch(key) {
    // Move to end (most recently used)
    const entry = this.map.get(key);
    if (entry !== undefined) {
      this.map.delete(key);
      this.map.set(key, entry);
    }
  }

  set(key, value, ttlMs) {
    const effectiveTtl = ttlMs ?? this.defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : this.now() + effectiveTtl;

    // If key already exists, update it
    if (this.map.has(key)) {
      this.map.delete(key);
    } else {
      // Check if we need to evict
      while (this.map.size >= this.capacity) {
        // First try to evict expired entries
        let evictedExpired = false;
        const now = this.now();
        for (const [k, entry] of this.map) {
          if (entry.expiry !== Infinity && now >= entry.expiry) {
            this.map.delete(k);
            evictedExpired = true;
            break;
          }
        }
        if (!evictedExpired) {
          // Evict LRU
          this._evictLru();
          break;
        }
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
    this._touch(key);
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
    // Map iteration order is insertion order; most recently used is at the end.
    // We need most recently used first, so reverse.
    return [...this.map.keys()].reverse();
  }
}
