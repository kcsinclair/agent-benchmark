export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    // Map preserves insertion order; we re-insert on access to move to end (MRU).
    // value: { value, expiry }
    this.map = new Map();
  }

  #isExpired(entry) {
    const expiry = entry.expiry;
    if (expiry === Infinity) return false;
    return this.now() >= expiry;
  }

  #purgeExpired() {
    // Remove all expired entries.
    for (const [key, entry] of this.map) {
      if (this.#isExpired(entry)) {
        this.map.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs ?? this.defaultTtlMs;
    const expiry = this.now() + ttl;
    // If key exists, remove it first so re-insertion moves it to MRU.
    if (this.map.has(key)) {
      this.map.delete(key);
    }
    this.map.set(key, { value, expiry });

    // Evict if over capacity: first expired, then LRU.
    while (this.map.size > this.capacity) {
      // Try to find an expired entry to evict.
      let evicted = false;
      for (const [k, entry] of this.map) {
        if (this.#isExpired(entry)) {
          this.map.delete(k);
          evicted = true;
          break;
        }
      }
      if (evicted) continue;
      // No expired entries; evict LRU (first key in map).
      const lruKey = this.map.keys().next().value;
      this.map.delete(lruKey);
    }
    return this;
  }

  get(key) {
    const entry = this.map.get(key);
    if (entry === undefined) return undefined;
    if (this.#isExpired(entry)) {
      this.map.delete(key);
      return undefined;
    }
    // Move to MRU.
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.map.get(key);
    if (entry === undefined) return false;
    if (this.#isExpired(entry)) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.map.delete(key);
  }

  get size() {
    this.#purgeExpired();
    return this.map.size;
  }

  keys() {
    this.#purgeExpired();
    // Map iteration is insertion order (LRU -> MRU); reverse for MRU -> LRU.
    return [...this.map.keys()].reverse();
  }
}
