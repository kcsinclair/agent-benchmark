// cache.mjs
// LRU cache with per-entry TTL. Node 20+, ES module, no dependencies.
//
// Recency is tracked by Map insertion order: the first key is the least
// recently used and the last key is the most recently used. To "touch" an
// entry, it is deleted and re-inserted, which moves it to the end.

function validateTtl(ttl, name) {
  if (typeof ttl !== 'number' || Number.isNaN(ttl)) {
    throw new TypeError(`${name} must be a number (got ${String(ttl)})`);
  }
}

export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  /** @type {Map<any, {value: any, expiresAt: number}>} */
  #map = new Map();
  // A lower bound on the smallest expiry among stored entries. If now() is
  // below it, nothing can be expired, so a full scan is unnecessary.
  #minExpiry = Infinity;

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

  #isExpired(entry, t) {
    // Infinity never expires: t >= Infinity is always false for a finite t.
    return entry.expiresAt !== Infinity && t >= entry.expiresAt;
  }

  // Remove every expired entry. The scan is skipped when no entry can be
  // expired yet. After a scan, #minExpiry is recomputed exactly.
  #purgeExpired() {
    const t = this.#now();
    if (t < this.#minExpiry) return;
    let min = Infinity;
    for (const [key, entry] of this.#map) {
      if (this.#isExpired(entry, t)) {
        this.#map.delete(key); // Deleting during Map iteration is safe.
      } else if (entry.expiresAt < min) {
        min = entry.expiresAt;
      }
    }
    this.#minExpiry = min;
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs ?? this.#defaultTtlMs;
    validateTtl(ttl, 'ttlMs');
    const expiresAt = ttl === Infinity ? Infinity : this.#now() + ttl;

    // Re-insert so the entry becomes the most recently used.
    this.#map.delete(key);
    this.#map.set(key, { value, expiresAt });
    if (expiresAt < this.#minExpiry) this.#minExpiry = expiresAt;

    if (this.#map.size > this.#capacity) {
      // Evict expired entries first.
      this.#purgeExpired();
      // If still over capacity, evict the least recently used entry.
      while (this.#map.size > this.#capacity) {
        const lruKey = this.#map.keys().next().value;
        this.#map.delete(lruKey);
      }
    }
    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return undefined;
    if (this.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return undefined;
    }
    // Mark as most recently used.
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return false;
    if (this.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return false;
    }
    return true; // Recency is intentionally not changed.
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
    // Map order is least to most recent; return most to least recent.
    return Array.from(this.#map.keys()).reverse();
  }
}
