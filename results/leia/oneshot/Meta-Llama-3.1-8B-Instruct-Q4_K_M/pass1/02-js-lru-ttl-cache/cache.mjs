// cache.mjs
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer ≥ 1');
    }

    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.cache = new Map();
    this.expiryMap = new Map();
  }

  set(key, value, ttlMs?) {
    const expiryTime = ttlMs !== undefined ? this.now() + (ttlMs ?? this.defaultTtlMs) : Infinity;
    if (expiryTime <= this.now()) {
      this.delete(key);
    } else {
      this.cache.set(key, { value, expiryTime });
      this.expiryMap.set(expiryTime, key);
      this.prune();
    }
    return this;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (entry === undefined || entry.expiryTime <= this.now()) {
      return undefined;
    }
    this.cache.delete(key);
    this.expiryMap.delete(entry.expiryTime);
    this.cache.set(key, { value: entry.value, expiryTime: entry.expiryTime });
    this.expiryMap.set(entry.expiryTime, key);
    return entry.value;
  }

  has(key) {
    const entry = this.cache.get(key);
    if (entry === undefined || entry.expiryTime <= this.now()) {
      this.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    const entry = this.cache.get(key);
    if (entry !== undefined) {
      this.cache.delete(key);
      this.expiryMap.delete(entry.expiryTime);
      return true;
    }
    return false;
  }

  get size() {
    this.prune();
    return this.cache.size;
  }

  keys() {
    this.prune();
    return Array.from(this.cache.keys());
  }

  prune() {
    const now = this.now();
    while (this.cache.size > this.capacity && this.expiryMap.size > 0) {
      const expiryTime = Math.min(...this.expiryMap.keys());
      if (expiryTime <= now) {
        const key = this.expiryMap.get(expiryTime);
        this.cache.delete(key);
        this.expiryMap.delete(expiryTime);
      } else {
        break;
      }
    }
  }
}
