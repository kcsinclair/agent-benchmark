// cache.mjs
// LRU cache with per-entry TTL. Recency is tracked with a Map's insertion
// order: the first entry is the least recently used, the last is the most
// recently used.

export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #map; // key -> { value, expiresAt }

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    LruTtlCache.#validateTtl(defaultTtlMs, 'defaultTtlMs');
    if (typeof now !== 'function') {
      throw new TypeError('now must be a function');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#map = new Map();
  }

  static #validateTtl(ttl, name) {
    if (typeof ttl !== 'number' || Number.isNaN(ttl)) {
      throw new TypeError(`${name} must be a number`);
    }
  }

  static #isExpired(entry, t) {
    return entry.expiresAt !== Infinity && t >= entry.expiresAt;
  }

  #purgeExpired(t) {
    for (const [key, entry] of this.#map) {
      if (LruTtlCache.#isExpired(entry, t)) this.#map.delete(key);
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs ?? this.#defaultTtlMs;
    LruTtlCache.#validateTtl(ttl, 'ttlMs');
    const t = this.#now();
    const expiresAt = ttl === Infinity ? Infinity : t + ttl;

    // Remove any existing entry so re-insertion makes it most recently used.
    const existed = this.#map.delete(key);

    // Already-expired entries (ttl <= 0) behave as absent; storing them
    // would only risk evicting live entries.
    if (expiresAt !== Infinity && t >= expiresAt) {
      return this;
    }

    if (!existed && this.#map.size >= this.#capacity) {
      this.#purgeExpired(t);
      while (this.#map.size >= this.#capacity) {
        const lruKey = this.#map.keys().next().value;
        this.#map.delete(lruKey);
      }
    }

    this.#map.set(key, { value, expiresAt });
    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return undefined;
    if (LruTtlCache.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return undefined;
    }
    // Move to most-recently-used position.
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return false;
    if (LruTtlCache.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    this.#purgeExpired(this.#now());
    return this.#map.size;
  }

  keys() {
    this.#purgeExpired(this.#now());
    return Array.from(this.#map.keys()).reverse();
  }
}
