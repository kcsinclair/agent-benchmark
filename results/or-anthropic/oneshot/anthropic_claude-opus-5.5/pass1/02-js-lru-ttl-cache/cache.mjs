// cache.mjs
// LRU cache with per-entry TTL. Uses an injected clock (`now`) for all time math.

function validateTtl(ttl, name) {
  if (typeof ttl !== 'number' || Number.isNaN(ttl)) {
    throw new TypeError(`${name} must be a number (got ${String(ttl)})`);
  }
}

export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map keeps insertion order: first entry = least recently used,
  // last entry = most recently used.
  #map = new Map(); // key -> { value, expiresAt }

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError(`capacity must be an integer >= 1 (got ${String(capacity)})`);
    }
    validateTtl(defaultTtlMs, 'defaultTtlMs');
    if (typeof now !== 'function') {
      throw new TypeError('now must be a function returning milliseconds');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  // An entry is expired when now >= expiresAt; Infinity never expires.
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
    validateTtl(ttl, 'ttlMs');
    const t = this.#now();
    const expiresAt = ttl === Infinity ? Infinity : t + ttl;

    // Remove any existing entry so re-insertion moves it to MRU position.
    this.#map.delete(key);

    // An entry that is already expired on arrival (ttl <= 0) would be
    // invisible to every read; storing it could only evict live entries.
    if (expiresAt !== Infinity && t >= expiresAt) return this;

    if (this.#map.size >= this.#capacity) {
      this.#purgeExpired(t);
      while (this.#map.size >= this.#capacity) {
        // Evict least recently used (first in insertion order).
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
    // Refresh recency.
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
    return Array.from(this.#map.keys()).reverse(); // MRU -> LRU
  }
}
