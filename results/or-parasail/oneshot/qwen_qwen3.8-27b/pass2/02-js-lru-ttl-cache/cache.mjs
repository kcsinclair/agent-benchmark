export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map preserves insertion order; we use it for LRU ordering.
    // Each entry: { value, expiry }
    this._map = new Map();
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  _purgeExpired() {
    // Remove all expired entries from the map
    for (const [key, entry] of this._map) {
      if (this._isExpired(entry)) {
        this._map.delete(key);
      }
    }
  }

  _evictIfNeeded() {
    // First, purge expired entries
    this._purgeExpired();
    // If still over capacity, evict LRU (first entry in map)
    while (this._map.size > this._capacity) {
      const firstKey = this._map.keys().next().value;
      this._map.delete(firstKey);
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;
    
    // If key exists, delete it first to re-insert at end (most recent)
    if (this._map.has(key)) {
      this._map.delete(key);
    }
    
    this._map.set(key, { value, expiry });
    
    // Evict if over capacity
    this._evictIfNeeded();
    
    return this;
  }

  get(key) {
    const entry = this._map.get(key);
    if (entry === undefined) {
      return undefined;
    }
    
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    
    // Move to most recently used: delete and re-insert
    this._map.delete(key);
    this._map.set(key, entry);
    
    return entry.value;
  }

  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) {
      return false;
    }
    
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }
    
    return true;
  }

  delete(key) {
    const entry = this._map.get(key);
    if (entry === undefined) {
      return false;
    }
    
    // If expired, still remove it
    this._map.delete(key);
    return true;
  }

  get size() {
    // Purge expired entries and return count
    this._purgeExpired();
    return this._map.size;
  }

  keys() {
    // Return live keys from most recently used to least recently used
    // Map iteration order is insertion order, so last inserted is most recent
    // We need to reverse: most recent first
    this._purgeExpired();
    const keys = Array.from(this._map.keys());
    return keys.reverse();
  }
}
