export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (capacity < 1) {
      throw new RangeError('capacity must be at least 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.cache = new Map();
    this.order = [];
  }

  set(key, value, ttlMs = this.defaultTtlMs) {
    const expiryTime = this.now() + ttlMs;
    const entry = { value, expiryTime };

    // Check if key exists and update it
    if (this.cache.has(key)) {
      const index = this.order.indexOf(key);
      this.order.splice(index, 1);
      this.cache.set(key, entry);
      this.order.push(key);
      return this;
    }

    // Check if we need to evict expired entries
    this.purgeExpired();

    // Check if we need to evict the least recently used entry
    if (this.cache.size >= this.capacity) {
      const lruKey = this.order.shift();
      this.cache.delete(lruKey);
    }

    // Add the new entry
    this.cache.set(key, entry);
    this.order.push(key);

    return this;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (!entry || this.now() >= entry.expiryTime) {
      // Entry is expired or doesn't exist
      this.purgeExpired();
      return undefined;
    }

    // Update recency
    const index = this.order.indexOf(key);
    this.order.splice(index, 1);
    this.order.push(key);

    return entry.value;
  }

  has(key) {
    const entry = this.cache.get(key);
    if (!entry) return false;

    // Check if expired
    if (this.now() >= entry.expiryTime) {
      this.purgeExpired();
      return false;
    }

    return true;
  }

  delete(key) {
    if (!this.cache.has(key)) return false;
    this.cache.delete(key);
    const index = this.order.indexOf(key);
    if (index !== -1) {
      this.order.splice(index, 1);
    }
    return true;
  }

  get size() {
    this.purgeExpired();
    return this.cache.size;
  }

  keys() {
    this.purgeExpired();
    return [...this.order];
  }

  purgeExpired() {
    const now = this.now();
    for (let i = 0; i < this.order.length; i++) {
      const key = this.order[i];
      const entry = this.cache.get(key);
      if (entry && entry.expiryTime !== Infinity && now >= entry.expiryTime) {
        this.cache.delete(key);
        this.order.splice(i, 1);
        i--;
      }
    }
  }
}
