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
    // Evict the least recently used entry (first in the Map)
    if (this.map.size > 0) {
      const firstKey = this.map.keys().next().value;
      this.map.delete(firstKey);
    }
  }

  set(key, value, ttlMs) {
    const effectiveTtl = ttlMs ?? this.defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : this.now() + effectiveTtl;
    const entry = { value, expiry };

    if (this.map.has(key)) {
      // Update existing entry: update value, expiry, and move to end (most recent)
      this.map.set(key, entry);
      this.map.delete(key);
      this.map.set(key, entry);
      return this;
    }

    // Check if we need to evict
    if (this.map.size >= this.capacity) {
      // First, try to evict expired entries
      this._purgeExpired();
      // If still at capacity, evict LRU
      if (this.map.size >= this.capacity) {
        this._evictLru();
      }
    }

    this.map.set(key, entry);
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

    // Move to end to mark as most recently used
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
    if (this.map.has(key)) {
      this.map.delete(key);
      return true;
    }
    return false;
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    // Map iteration order is insertion order, which we maintain as recency order
    // (most recently used at the end). We need most recently used first.
    const result = [];
    for (const key of this.map.keys()) {
      result.push(key);
    }
    // Reverse to get most recently used first
    return result.reverse();
  }
}
