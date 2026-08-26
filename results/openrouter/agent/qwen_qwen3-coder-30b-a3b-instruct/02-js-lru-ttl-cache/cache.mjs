export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer greater than or equal to 1');
    }
    
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.cache = new Map(); // key -> { value, expiryTime }
  }

  set(key, value, ttlMs = this.defaultTtlMs) {
    const expiryTime = ttlMs === Infinity ? Infinity : this.now() + ttlMs;
    
    // Check if we need to evict entries before inserting
    if (this.cache.size >= this.capacity) {
      this._evictExpired();
      if (this.cache.size >= this.capacity) {
        // Remove the least recently used entry (the first one in the map)
        const firstKey = this.cache.keys().next().value;
        this.cache.delete(firstKey);
      }
    }
    
    this.cache.set(key, { value, expiryTime });
    return this;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (entry === undefined) {
      return undefined;
    }
    
    // Check if expired
    if (entry.expiryTime !== Infinity && this.now() >= entry.expiryTime) {
      this.cache.delete(key);
      return undefined;
    }
    
    // Move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, entry);
    
    return entry.value;
  }

  has(key) {
    const entry = this.cache.get(key);
    if (entry === undefined) {
      return false;
    }
    
    // Check if expired
    if (entry.expiryTime !== Infinity && this.now() >= entry.expiryTime) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  delete(key) {
    return this.cache.delete(key);
  }

  get size() {
    // Purge expired entries and return count of live entries
    this._evictExpired();
    return this.cache.size;
  }

  keys() {
    // Purge expired entries and return keys in LRU order
    this._evictExpired();
    return Array.from(this.cache.keys());
  }

  _evictExpired() {
    const now = this.now();
    for (const [key, entry] of this.cache.entries()) {
      if (entry.expiryTime !== Infinity && now >= entry.expiryTime) {
        this.cache.delete(key);
      }
    }
  }
}
