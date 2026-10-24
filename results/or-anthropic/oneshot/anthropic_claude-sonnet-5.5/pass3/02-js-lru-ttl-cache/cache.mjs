// cache.mjs
export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map preserves insertion order: first = least recently used, last = most recently used.
  #map = new Map();

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  static #isExpired(entry, t) {
    return entry.expiry !== Infinity && t >= entry.expiry;
  }

  #purgeExpired(t) {
    // Deleting entries during Map iteration is safe.
    for (const [k, e] of this.#map) {
      if (LruTtlCache.#isExpired(e, t)) this.#map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const t = this.#now();
    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiry = t + ttl;

    // Remove any existing entry (so a replacement moves to the MRU position
    // and never triggers eviction of other entries).
    this.#map.delete(key);

    // Already expired (ttl <= 0): nothing live to store. Don't evict live entries for it.
    if (ttl !== Infinity && t >= expiry) {
      return this;
    }

    if (this.#map.size >= this.#capacity) {
      this.#purgeExpired(t);
      while (this.#map.size >= this.#capacity) {
        const oldest = this.#map.keys().next().value;
        this.#map.delete(oldest);
      }
    }

    this.#map.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return undefined;
    if (LruTtlCache.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return undefined;
    }
    // Move to most recently used.
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
