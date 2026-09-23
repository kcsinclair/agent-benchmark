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
    // Map preserves insertion order; we keep MRU at the end.
    this.#map = new Map();
  }

  #isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this.#now() >= expiry;
  }

  #purge(key) {
    this.#map.delete(key);
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs === undefined ? this.#defaultTtlMs : ttlMs;
    const expiry = ttl === Infinity ? Infinity : this.#now() + ttl;

    // Remove existing so re-insertion puts it at the end (MRU).
    this.#map.delete(key);

    // If already expired, don't store it at all (matches get()/has() semantics).
    if (this.#isExpired(expiry)) {
      return this;
    }

    this.#map.set(key, { value, expiry });

    if (this.#map.size > this.#capacity) {
      this.#evict();
    }
    return this;
  }

  #evict() {
    // First pass: drop expired entries (scanning from LRU side is fine).
    // We must be careful because iterating and mutating is allowed for Map
    // as long as we delete the current entry.
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry.expiry)) {
        this.#map.delete(k);
        if (this.#map.size <= this.#capacity) return;
      }
    }
    // Still over capacity: evict LRU (first inserted).
    while (this.#map.size > this.#capacity) {
      const oldest = this.#map.keys().next().value;
      this.#map.delete(oldest);
    }
  }

  get(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return undefined;
    if (this.#isExpired(entry.expiry)) {
      this.#map.delete(key);
      return undefined;
    }
    // Move to MRU (end).
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return false;
    if (this.#isExpired(entry.expiry)) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    // Purge expired entries so `size` reflects only live entries.
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry.expiry)) {
        this.#map.delete(k);
      }
    }
    return this.#map.size;
  }

  keys() {
    const result = [];
    for (const [k, entry] of this.#map) {
      if (!this.#isExpired(entry.expiry)) {
        result.push(k);
      }
    }
    // Reverse to order MRU -> LRU.
    result.reverse();
    return result;
  }
}
