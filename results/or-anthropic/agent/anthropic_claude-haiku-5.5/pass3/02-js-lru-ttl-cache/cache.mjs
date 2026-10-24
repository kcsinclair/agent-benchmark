export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map preserves insertion order; we re-insert on access so that the
  // first entry is the least recently used and the last is the most recent.
  #map = new Map();

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  #expiryFor(ttlMs) {
    const ttl = ttlMs === undefined || ttlMs === null ? this.#defaultTtlMs : ttlMs;
    if (ttl === Infinity) return Infinity;
    return this.#now() + ttl;
  }

  #isExpired(entry, t = this.#now()) {
    return entry.expiresAt !== Infinity && t >= entry.expiresAt;
  }

  #purgeExpired() {
    const t = this.#now();
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry, t)) this.#map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const expiresAt = this.#expiryFor(ttlMs);
    if (this.#map.has(key)) {
      this.#map.delete(key);
    }
    this.#map.set(key, { value, expiresAt });
    if (this.#map.size > this.#capacity) {
      this.#purgeExpired();
      while (this.#map.size > this.#capacity) {
        const oldest = this.#map.keys().next().value;
        this.#map.delete(oldest);
      }
    }
    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return undefined;
    if (this.#isExpired(entry)) {
      this.#map.delete(key);
      return undefined;
    }
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return false;
    if (this.#isExpired(entry)) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    this.#purgeExpired();
    return this.#map.size;
  }

  keys() {
    this.#purgeExpired();
    return [...this.#map.keys()].reverse();
  }
}
