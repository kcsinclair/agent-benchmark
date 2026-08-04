export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #cache;

  /**
   * @param {Object} options
   * @param {number} options.capacity - Maximum number of non-expired entries.
   * @param {number} [options.defaultTtlMs=Infinity] - Default TTL in milliseconds.
   * @param {Function} [options.now=() => Date.now()] - Clock function.
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    // Map preserves insertion order. 
    // We treat the "end" of the map as the Most Recently Used (MRU) 
    // and the "start" as the Least Recently Used (LRU).
    this.#cache = new Map();
  }

  /**
   * @param {*} key
   * @param {*} value
   * @param {number} [ttlMs]
   * @returns {LruTtlCache}
   */
  set(key, value, ttlMs) {
    const currentTime = this.#now();
    const ttl = ttlMs !== undefined ? ttlMs : this.#defaultTtlMs;
    const expiry = currentTime + ttl;

    // If key exists, remove it first to update its position to MRU
    if (this.#cache.has(key)) {
      this.#cache.delete(key);
    }

    // Check if we need to evict before adding new entry
    // 1. Purge expired entries to make room if possible
    this.#purgeExpired();

    // 2. If still at capacity, evict the LRU (the first item in the Map)
    if (this.#cache.size >= this.#capacity) {
      const lruKey = this.#cache.keys().next().value;
      this.#cache.delete(lruKey);
    }

    this.#cache.set(key, { value, expiry });
    return this;
  }

  /**
   * @param {*} key
   * @returns {*}
   */
  get(key) {
    const entry = this.#cache.get(key);
    if (entry === undefined) return undefined;

    if (this.#now() >= entry.expiry) {
      this.#cache.delete(key);
      return undefined;
    }

    // Refresh recency: delete and re-insert to move to the end (MRU)
    this.#cache.delete(key);
    this.#cache.set(key, entry);
    return entry.value;
  }

  /**
   * @param {*} key
   * @returns {boolean}
   */
  has(key) {
    const entry = this.#cache.get(key);
    if (entry === undefined) return false;

    if (this.#now() >= entry.expiry) {
      this.#cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * @param {*} key
   * @returns {boolean}
   */
  delete(key) {
    return this.#cache.delete(key);
  }

  /**
   * @returns {number}
   */
  get size() {
    this.#purgeExpired();
    return this.#cache.size;
  }

  /**
   * @returns {Array<*>}
   */
  keys() {
    this.#purgeExpired();
    // Map keys are in insertion order (LRU -> MRU). 
    // Requirement: "ordered from most recently used to least recently used".
    return Array.from(this.#cache.keys()).reverse();
  }

  /**
   * Internal helper to remove expired entries.
   */
  #purgeExpired() {
    const currentTime = this.#now();
    for (const [key, entry] of this.#cache.entries()) {
      if (currentTime >= entry.expiry) {
        this.#cache.delete(key);
      }
    }
  }
}
