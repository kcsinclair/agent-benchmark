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
    return this.cache.size;
  }

  keys() {
    const keys = [];
    for (const [expiryTime, key] of this.expiryMap) {
      keys.push(key);
    }
    return keys;
  }

  prune() {
    while (this.cache.size > this.capacity) {
      const expiryTime = Math.min(...this.expiryMap.keys());
      if (expiryTime <= this.now()) {
        this.expiryMap.delete(expiryTime);
        this.cache.delete(this.expiryMap.get(expiryTime));
      } else {
        break;
      }
    }
  }
}
