export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (typeof capacity !== 'number' || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }

    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.cache = new Map();
    this.order = []; // maintain order for LRU
  }

  set(key, value, ttlMs) {
    const expiryTime = ttlMs !== undefined ? this.now() + (ttlMs ?? this.defaultTtlMs) : this.now() + this.defaultTtlMs;
    
    // Check if key exists and is expired
    if (this.cache.has(key)) {
      const entry = this.cache.get(key);
      entry.value = value;
      entry.expiry = expiryTime;
      this.order.splice(this.order.indexOf(key), 1);
      this.order.push(key);
      return this;
    }

    // Check if we need to evict expired entries
    this.purgeExpired();

    // Check if we need to evict to make room
    if (this.cache.size >= this.capacity) {
      this.evictLeastRecentlyUsed();
    }

    // Add new entry
    this.cache.set(key, {
      value,
      expiry: expiryTime
    });
    this.order.push(key);
    return this;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (!entry) {
      return undefined;
    }

    // Check if expired
    if (entry.expiry !== Infinity && this.now() >= entry.expiry) {
      this.cache.delete(key);
      this.order.splice(this.order.indexOf(key), 1);
      return undefined;
    }

    // Update recency
    this.order.splice(this.order.indexOf(key), 1);
    this.order.push(key);
    return entry.value;
  }

  has(key) {
    const entry = this.cache.get(key);
    if (!entry) {
      return false;
    }

    // Check if expired
    if (entry.expiry !== Infinity && this.now() >= entry.expiry) {
      this.cache.delete(key);
      this.order.splice(this.order.indexOf(key), 1);
      return false;
    }

    return true;
  }

  delete(key) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
      this.order.splice(this.order.indexOf(key), 1);
      return true;
    }
    return false;
  }

  get size() {
    this.purgeExpired();
    return this.cache.size;
  }

  keys() {
    this.purgeExpired();
    return [...this.order];
  }

  // Helper methods
  purgeExpired() {
    const now = this.now();
    for (const key of this.order) {
      const entry = this.cache.get(key);
      if (entry && entry.expiry !== Infinity && now >= entry.expiry) {
        this.cache.delete(key);
        this.order.splice(this.order.indexOf(key), 1);
      }
    }
  }

  evictLeastRecentlyUsed() {
    const leastRecentlyUsed = this.order.shift();
    if (leastRecentlyUsed) {
      this.cache.delete(leastRecentlyUsed);
    }
  }
}
