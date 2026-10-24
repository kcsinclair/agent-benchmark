// LRU cache with per-entry TTL. Recency order is kept by Map insertion
// order: the first entry is least recently used, the last is most recent.

function checkTtl(ttl, name) {
  if (typeof ttl !== 'number' || Number.isNaN(ttl)) {
    throw new TypeError(`${name} must be a number`);
  }
}

export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    checkTtl(defaultTtlMs, 'defaultTtlMs');
    if (typeof now !== 'function') throw new TypeError('now must be a function');
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> { value, expiresAt }
    // Lower bound on the earliest expiry among stored entries; lets us skip
    // full purge scans when nothing can have expired yet.
    this._minExpiry = Infinity;
  }

  static _expired(entry, t) {
    return entry.expiresAt !== Infinity && t >= entry.expiresAt;
  }

  _purge(t) {
    if (t < this._minExpiry) return;
    let min = Infinity;
    for (const [k, e] of this._map) {
      if (LruTtlCache._expired(e, t)) this._map.delete(k);
      else if (e.expiresAt < min) min = e.expiresAt;
    }
    this._minExpiry = min;
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs ?? this._defaultTtlMs;
    checkTtl(ttl, 'ttlMs');
    const t = this._now();
    const map = this._map;
    map.delete(key);
    if (ttl <= 0) {
      // Already expired: never stored, and must not evict live entries.
      return this;
    }
    const expiresAt = ttl === Infinity ? Infinity : t + ttl;
    if (map.size >= this._capacity) {
      this._purge(t);
      while (map.size >= this._capacity) {
        const lruKey = map.keys().next().value;
        map.delete(lruKey);
      }
    }
    map.set(key, { value, expiresAt });
    if (expiresAt < this._minExpiry) this._minExpiry = expiresAt;
    return this;
  }

  get(key) {
    const map = this._map;
    const entry = map.get(key);
    if (entry === undefined) return undefined;
    map.delete(key);
    if (LruTtlCache._expired(entry, this._now())) return undefined;
    map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;
    if (LruTtlCache._expired(entry, this._now())) {
      this._map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    const entry = this._map.get(key);
    if (entry === undefined) return false;
    this._map.delete(key);
    // An expired entry was logically already gone.
    return !LruTtlCache._expired(entry, this._now());
  }

  get size() {
    this._purge(this._now());
    return this._map.size;
  }

  keys() {
    this._purge(this._now());
    const out = Array.from(this._map.keys());
    out.reverse();
    return out;
  }
}

export default LruTtlCache;
