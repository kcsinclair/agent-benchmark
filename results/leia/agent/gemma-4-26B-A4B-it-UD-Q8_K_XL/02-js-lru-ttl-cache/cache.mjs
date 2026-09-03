export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._cache = new Map();
  }

  _isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this._now() >= expiry;
  }

  set(key, value, ttlMs) {
    const expiry = this._now() + (ttlMs ?? this._defaultTtlMs);

    if (this._cache.has(key)) {
      this._cache.delete(key);
      this._cache.set(key, { value, expiry });
      return this;
    }

    if (this._cache.size >= this._capacity) {
      let expiredKey = null;
      for (const [k, entry] of this._cache.entries()) {
        if (this._isExpired(entry.expiry)) {
          expiredKey = k;
          break;
        }
      }

      if (expiredKey !== null) {
        this._cache.delete(expiredKey);
      } else {
        const firstKey = this._cache.keys().next().value;
        this._cache.delete(firstKey);
      }
    }

    this._cache.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry.expiry)) {
      this._cache.delete(key);
      return undefined;
    }

    this._cache.delete(key);
    this._cache.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._cache.get(key);
    if (!entry) return false;

    if (this._isExpired(entry.expiry)) {
      this._cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this._cache.delete(key);
  }

  get size() {
    for (const [k, entry] of this._cache.entries()) {
      if (this._isExpired(entry.expiry)) {
        this._cache.delete(k);
      }
    }
    return this._cache.size;
  }

  keys() {
    const liveKeys = [];
    for (const [k, entry] of this._cache.entries()) {
      if (!this._isExpired(entry.expiry)) {
        liveKeys.push(k);
      } else {
        this._cache.delete(k);
      }
    }
    return liveKeys.reverse();
  }
}
