export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map preserves insertion order: first = least recently used, last = most recent.
  #map = new Map();

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (typeof capacity !== 'number' || !Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    if (typeof now !== 'function') {
      throw new TypeError('now must be a function');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  #isExpired(entry, t = this.#now()) {
    if (entry.expiresAt === Infinity) return false;
    // NaN expiry is treated as expired
    return !(t < entry.expiresAt);
  }

  #purgeExpired() {
    const t = this.#now();
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry, t)) this.#map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs ?? this.#defaultTtlMs;
    const t = this.#now();
    const expiresAt = ttl === Infinity ? Infinity : t + ttl;

    // Replacing: remove the old entry so re-insertion moves it to MRU position.
    this.#map.delete(key);

    const entry = { value, expiresAt };
    if (this.#isExpired(entry, t)) {
      // Already expired (ttl <= 0): it would never be observable; don't evict live entries for it.
      return this;
    }

    if (this.#map.size >= this.#capacity) {
      this.#purgeExpired();
      while (this.#map.size >= this.#capacity) {
        const oldest = this.#map.keys().next().value;
        this.#map.delete(oldest);
      }
    }
    this.#map.set(key, entry);
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
    const entry = this.#map.get(key);
    if (entry === undefined) return false;
    this.#map.delete(key);
    return !this.#isExpired(entry);
  }

  get size() {
    this.#purgeExpired();
    return this.#map.size;
  }

  keys() {
    this.#purgeExpired();
    return Array.from(this.#map.keys()).reverse();
  }
}
