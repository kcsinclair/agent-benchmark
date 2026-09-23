export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.cache = new Map(); // key -> { value, expiryTime }
  }

  /**
   * Remove expired entries from the cache.
   */
  #purgeExpired() {
    const currentTime = this.now();
    for (const [key, entry] of this.cache.entries()) {
      if (entry.expiryTime !== Infinity && currentTime >= entry.expiryTime) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Check if an entry is expired.
   */
  #isExpired(entry) {
    if (entry.expiryTime === Infinity) {
      return false;
    }
    return this.now() >= entry.expiryTime;
  }

  /**
   * Set a key-value pair with optional TTL.
   * Returns this for chaining.
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiryTime = ttl === Infinity ? Infinity : this.now() + ttl;

    // If key already exists, delete it first to update recency
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }

    // Add the entry (Map maintains insertion order, so this becomes most recent)
    this.cache.set(key, { value, expiryTime });

    // Evict if necessary
    if (this.cache.size > this.capacity) {
      // First, purge expired entries
      this.#purgeExpired();

      // If still over capacity, evict LRU (first entry in Map)
      if (this.cache.size > this.capacity) {
        const firstKey = this.cache.keys().next().value;
        this.cache.delete(firstKey);
      }
    }

    return this;
  }

  /**
   * Get a value by key. Returns undefined if absent or expired.
   * Makes the entry most recently used.
   */
  get(key) {
    if (!this.cache.has(key)) {
      return undefined;
    }

    const entry = this.cache.get(key);

    // Check if expired
    if (this.#isExpired(entry)) {
      this.cache.delete(key);
      return undefined;
    }

    // Update recency by deleting and re-inserting
    this.cache.delete(key);
    this.cache.set(key, entry);

    return entry.value;
  }

  /**
   * Check if a key exists and is not expired.
   * Does not affect recency.
   * Removes the entry if expired.
   */
  has(key) {
    if (!this.cache.has(key)) {
      return false;
    }

    const entry = this.cache.get(key);

    // Check if expired
    if (this.#isExpired(entry)) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete a key. Returns true if something was removed.
   */
  delete(key) {
    return this.cache.delete(key);
  }

  /**
   * Get the number of live (non-expired) entries.
   */
  get size() {
    this.#purgeExpired();
    return this.cache.size;
  }

  /**
   * Get an array of live keys ordered from most recently used to least recently used.
   */
  keys() {
    this.#purgeExpired();
    return Array.from(this.cache.keys());
  }
}
