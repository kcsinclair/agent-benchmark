export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map keeps insertion order: first = least recently used, last = most recent.
  #map = new Map();

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    if (typeof now !== 'function') {
      throw new TypeError('now must be a function');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  static #expired(entry, t) {
    return entry.expiresAt !== Infinity && t >= entry.expiresAt;
  }

  #purge(t) {
    for (const [k, e] of this.#map) {
      if (LruTtlCache.#expired(e, t)) this.#map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const t = this.#now();
    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiresAt = ttl === Infinity ? Infinity : t + ttl;
    const map = this.#map;
    const existed = map.has(key);
    if (existed) map.delete(key);

    // Already-expired entries (ttl <= 0) are never observable; don't store
    // them so they can't cause eviction of live entries.
    if (expiresAt !== Infinity && !(t < expiresAt)) {
      return this;
    }

    if (!existed && map.size >= this.#capacity) {
      this.#purge(t);
      while (map.size >= this.#capacity) {
        const oldest = map.keys().next().value;
        map.delete(oldest);
      }
    }
    map.set(key, { value, expiresAt });
    return this;
  }

  get(key) {
    const map = this.#map;
    const e = map.get(key);
    if (e === undefined) return undefined;
    map.delete(key);
    if (LruTtlCache.#expired(e, this.#now())) return undefined;
    map.set(key, e);
    return e.value;
  }

  has(key) {
    const e = this.#map.get(key);
    if (e === undefined) return false;
    if (LruTtlCache.#expired(e, this.#now())) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    const e = this.#map.get(key);
    if (e === undefined) return false;
    this.#map.delete(key);
    // Expired entries are logically absent.
    return !LruTtlCache.#expired(e, this.#now());
  }

  get size() {
    this.#purge(this.#now());
    return this.#map.size;
  }

  keys() {
    this.#purge(this.#now());
    return Array.from(this.#map.keys()).reverse();
  }
}
