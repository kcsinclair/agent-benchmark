export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (typeof capacity !== 'number' || !Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map();
  }

  _isExpired(entry) {
    return entry.expiry !== Infinity && this.now() >= entry.expiry;
  }

  _purgeExpired() {
    const now = this.now();
    for (const [key, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
      }
    }
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.now() + ttl;

    if (this.map.has(key)) {
      this.map.delete(key);
      this.map.set(key, { value, expiry });
      return this;
    }

    if (this.map.size >= this.capacity) {
      this._purgeExpired();
      if (this.map.size >= this.capacity) {
        const lruKey = this.map.keys().next().value;
        this.map.delete(lruKey);
      }
    }

    this.map.set(key, { value, expiry });
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
    return this.map.delete(key);
  }

  keys() {
    this._purgeExpired();
    const result = [];
    for (const key of this.map.keys()) {
      result.push(key);
    }
    return result.reverse();
  }
}
