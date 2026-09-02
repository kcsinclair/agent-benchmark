export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #map;

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (typeof capacity !== 'number' || !Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#map = new Map();
  }

  #isExpired(expiresAt) {
    if (expiresAt === Infinity) return false;
    return this.#now() >= expiresAt;
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.#defaultTtlMs;
    const expiresAt = ttl === Infinity ? Infinity : this.#now() + ttl;

    if (this.#map.has(key)) {
      this.#map.delete(key);
    } else if (this.#map.size >= this.#capacity) {
      for (const [k, entry] of this.#map) {
        if (this.#isExpired(entry.expiresAt)) {
          this.#map.delete(k);
        }
      }

      if (this.#map.size >= this.#capacity) {
        const lruKey = this.#map.keys().next().value;
        this.#map.delete(lruKey);
      }
    }

    this.#map.set(key, { value, expiresAt });
    return this;
  }

  get(key) {
    if (!this.#map.has(key)) {
      return undefined;
    }

    const entry = this.#map.get(key);
    if (this.#isExpired(entry.expiresAt)) {
      this.#map.delete(key);
      return undefined;
    }

    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    if (!this.#map.has(key)) {
      return false;
    }

    const entry = this.#map.get(key);
    if (this.#isExpired(entry.expiresAt)) {
      this.#map.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry.expiresAt)) {
        this.#map.delete(k);
      }
    }
    return this.#map.size;
  }

  keys() {
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry.expiresAt)) {
        this.#map.delete(k);
      }
    }
    return Array.from(this.#map.keys()).reverse();
  }
}
