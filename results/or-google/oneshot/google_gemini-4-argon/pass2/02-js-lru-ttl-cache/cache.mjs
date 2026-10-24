// cache.mjs

export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #map;

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#map = new Map();
  }

  #isExpired(entry, currentTime = this.#now()) {
    return entry.expiresAt !== Infinity && currentTime >= entry.expiresAt;
  }

  #purgeExpired(currentTime = this.#now()) {
    for (const [key, entry] of this.#map.entries()) {
      if (this.#isExpired(entry, currentTime)) {
        this.#map.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const currentTime = this.#now();
    const effectiveTtl = ttlMs ?? this.#defaultTtlMs;

    if (this.#map.has(key)) {
      this.#map.delete(key);
    }

    // If ttlMs is 0 or negative (or NaN), it is already expired at `currentTime`.
    if (effectiveTtl <= 0 || Number.isNaN(effectiveTtl)) {
      return this;
    }

    if (this.#map.size >= this.#capacity) {
      this.#purgeExpired(currentTime);
      if (this.#map.size >= this.#capacity) {
        const lruKey = this.#map.keys().next().value;
        this.#map.delete(lruKey);
      }
    }

    const expiresAt = effectiveTtl === Infinity ? Infinity : currentTime + effectiveTtl;
    this.#map.set(key, { value, expiresAt });

    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (!entry) {
      return undefined;
    }

    if (this.#isExpired(entry)) {
      this.#map.delete(key);
      return undefined;
    }

    // Refresh recency by re-inserting
    this.#map.delete(key);
    this.#map.set(key, entry);

    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (!entry) {
      return false;
    }

    if (this.#isExpired(entry)) {
      this.#map.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    const entry = this.#map.get(key);
    if (!entry) {
      return false;
    }

    const expired = this.#isExpired(entry);
    this.#map.delete(key);
    return !expired;
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
