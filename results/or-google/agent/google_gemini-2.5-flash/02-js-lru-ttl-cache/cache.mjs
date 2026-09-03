export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #cache = new Map(); // Stores { value, expiry, lastUsed }
  #lru = []; // Stores keys in LRU order

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("Capacity must be an integer >= 1");
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  #purgeExpired() {
    const currentTime = this.#now();
    for (let i = this.#lru.length - 1; i >= 0; i--) {
      const key = this.#lru[i];
      const entry = this.#cache.get(key);
      if (entry && entry.expiry !== Infinity && currentTime >= entry.expiry) {
        this.#cache.delete(key);
        this.#lru.splice(i, 1);
      }
    }
  }

  #makeMostRecentlyUsed(key) {
    const index = this.#lru.indexOf(key);
    if (index !== -1) {
      this.#lru.splice(index, 1);
    }
    this.#lru.unshift(key);
  }

  set(key, value, ttlMs) {
    const currentTime = this.#now();
    const effectiveTtlMs = ttlMs ?? this.#defaultTtlMs;
    const expiry = effectiveTtlMs === Infinity ? Infinity : currentTime + effectiveTtlMs;

    if (effectiveTtlMs <= 0) {
      this.delete(key);
      return this;
    }

    if (this.#cache.has(key)) {
      this.#cache.set(key, { value, expiry });
      this.#makeMostRecentlyUsed(key);
    } else {
      this.#purgeExpired();
      if (this.#cache.size >= this.#capacity) {
        // Evict LRU if still over capacity
        const lruKey = this.#lru.pop();
        this.#cache.delete(lruKey);
      }
      this.#cache.set(key, { value, expiry });
      this.#lru.unshift(key);
    }
    return this;
  }

  get(key) {
    const entry = this.#cache.get(key);
    if (!entry) {
      return undefined;
    }

    const currentTime = this.#now();
    if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
      this.delete(key);
      return undefined;
    }

    this.#makeMostRecentlyUsed(key);
    return entry.value;
  }

  has(key) {
    const entry = this.#cache.get(key);
    if (!entry) {
      return false;
    }

    const currentTime = this.#now();
    if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
      this.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    if (this.#cache.delete(key)) {
      const index = this.#lru.indexOf(key);
      if (index !== -1) {
        this.#lru.splice(index, 1);
      }
      return true;
    }
    return false;
  }

  get size() {
    this.#purgeExpired();
    return this.#cache.size;
  }

  keys() {
    this.#purgeExpired();
    return [...this.#lru];
  }
}
