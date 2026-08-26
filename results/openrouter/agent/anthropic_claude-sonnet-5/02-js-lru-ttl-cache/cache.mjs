export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  _isExpired(entry, t) {
    if (entry.expiry === Infinity) return false;
    return t >= entry.expiry;
  }

  _purgeExpired(t) {
    for (const [key, entry] of this._map) {
      if (this._isExpired(entry, t)) {
        this._map.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const t = this.now();
    const effectiveTtl = ttlMs === undefined ? this.defaultTtlMs : ttlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : t + effectiveTtl;

    if (this._map.has(key)) {
      this._map.delete(key);
    }
    this._map.set(key, { value, expiry });

    if (this._map.size > this.capacity) {
      this._purgeExpired(t);
      while (this._map.size > this.capacity) {
        const oldestKey = this._map.keys().next().value;
        this._map.delete(oldestKey);
      }
    }

    return this;
  }

  get(key) {
    const t = this.now();
    const entry = this._map.get(key);
    if (entry === undefined) return undefined;
    if (this._isExpired(entry, t)) {
      this._map.delete(key);
      return undefined;
    }
    this._map.delete(key);
    this._map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const t = this.now();
    const entry = this._map.get(key);
    if (entry === undefined) return false;
    if (this._isExpired(entry, t)) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this._map.delete(key);
  }

  get size() {
    const t = this.now();
    this._purgeExpired(t);
    return this._map.size;
  }

  keys() {
    const t = this.now();
    this._purgeExpired(t);
    return Array.from(this._map.keys()).reverse();
  }
}
