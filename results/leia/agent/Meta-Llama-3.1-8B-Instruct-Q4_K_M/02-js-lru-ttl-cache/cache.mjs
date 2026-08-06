export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.cache = new Map();
  }

  set(key, value, ttlMs?) {
    const expiryTime = ttlMs !== undefined ? this.now() + (ttlMs ?? this.defaultTtlMs) : Infinity;
    this.cache.set(key, { value, expiryTime });
    this.cache.delete(key);
    this.cache.set(key, { value, expiryTime });
    return this;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (entry === undefined || entry.expiryTime <= this.now()) {
      return undefined;
    }
    this.cache.delete(key);
    this.cache.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.cache.get(key);
    if (entry === undefined || entry.expiryTime <= this.now()) {
      return false;
    }
    return true;
  }

  delete(key) {
    const deleted = this.cache.delete(key);
    return deleted;
  }

  get size() {
    let size = 0;
    for (const entry of this.cache.values()) {
      if (entry.expiryTime > this.now()) {
        size++;
      }
    }
    return size;
  }

  keys() {
    const keys = [];
    for (const [key, entry] of this.cache.entries()) {
      if (entry.expiryTime > this.now()) {
        keys.push(key);
      }
    }
    return keys;
  }
}
