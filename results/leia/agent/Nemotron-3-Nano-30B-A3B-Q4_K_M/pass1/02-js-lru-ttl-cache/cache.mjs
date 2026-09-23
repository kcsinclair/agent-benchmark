export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key => {value, expiry}
  }

  _now() {
    return this.now();
  }

  _purgeExpired() {
    const nowMs = this._now();
    const toDelete = [];
    for (const [k, entry] of this.map) {
      if (entry.expiry !== Infinity && nowMs >= entry.expiry) {
        toDelete.push(k);
      }
    }
    for (const k of toDelete) {
      this.map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const nowMs = this._now();
    const expiry = ttlMs !== undefined ? nowMs + ttlMs : nowMs + this.defaultTtlMs;
    const entry = { value, expiry };
    if (this.map.has(key)) {
      this.map.delete(key);
    }
    this.map.set(key, entry);
    this._purgeExpired();
    // enforce capacity
    while (this.map.size > this.capacity) {
      const firstKey = this.map.keys().next().value;
      if (firstKey === undefined) break;
      this.map.delete(firstKey);
    }
    return this;
  }

  get(key) {
    if (!this.map.has(key)) return undefined;
    const entry = this.map.get(key);
    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this.map.delete(key);
      return undefined;
    }
    // move to most recent
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  has(key) {
    if (!this.map.has(key)) return false;
    const entry = this.map.get(key);
    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    if (!this.map.has(key)) return false;
    this.map.delete(key);
    return true;
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    const keys = [];
    for (const [k] of this.map) {
      keys.push(k);
    }
    return keys.reverse();
  }
}
