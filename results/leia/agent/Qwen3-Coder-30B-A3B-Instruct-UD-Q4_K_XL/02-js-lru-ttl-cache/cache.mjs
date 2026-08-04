export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer ≥ 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key -> { value, expiryTime }
    this.accessOrder = new Map(); // key -> accessTime (for LRU)
  }

  set(key, value, ttlMs = this.defaultTtlMs) {
    const expiryTime = ttlMs === Infinity ? Infinity : this.now() + ttlMs;
    const accessTime = this.now();
    
    // Remove expired entries first
    this._purgeExpired();
    
    // If key exists, update it
    if (this.map.has(key)) {
      this.map.set(key, { value, expiryTime });
      this.accessOrder.set(key, accessTime);
      return this;
    }
    
    // If cache is at capacity, remove LRU entry
    if (this.map.size >= this.capacity) {
      const lruKey = this._getLruKey();
      if (lruKey !== undefined) {
        this.map.delete(lruKey);
        this.accessOrder.delete(lruKey);
      }
    }
    
    // Insert new entry
    this.map.set(key, { value, expiryTime });
    this.accessOrder.set(key, accessTime);
    return this;
  }

  get(key) {
    const entry = this.map.get(key);
    if (entry === undefined) {
      return undefined;
    }
    
    // Check if expired
    if (this.now() >= entry.expiryTime) {
      this.map.delete(key);
      this.accessOrder.delete(key);
      return undefined;
    }
    
    // Update access order
    this.accessOrder.set(key, this.now());
    return entry.value;
  }

  has(key) {
    const entry = this.map.get(key);
    if (entry === undefined) {
      return false;
    }
    
    // Check if expired
    if (this.now() >= entry.expiryTime) {
      this.map.delete(key);
      this.accessOrder.delete(key);
      return false;
    }
    
    return true;
  }

  delete(key) {
    const deleted = this.map.delete(key);
    this.accessOrder.delete(key);
    return deleted;
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    // Return keys ordered from most recently used to least recently used
    const sortedEntries = Array.from(this.accessOrder.entries())
      .sort((a, b) => b[1] - a[1]);
    return sortedEntries.map(([key]) => key);
  }

  _purgeExpired() {
    const now = this.now();
    for (const [key, entry] of this.map.entries()) {
      if (now >= entry.expiryTime) {
        this.map.delete(key);
        this.accessOrder.delete(key);
      }
    }
  }

  _getLruKey() {
    if (this.accessOrder.size === 0) {
      return undefined;
    }
    
    // Find the key with the earliest access time
    let lruKey = undefined;
    let earliestTime = Infinity;
    
    for (const [key, accessTime] of this.accessOrder.entries()) {
      if (accessTime < earliestTime) {
        earliestTime = accessTime;
        lruKey = key;
      }
    }
    
    return lruKey;
  }
}
