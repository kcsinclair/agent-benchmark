export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    // Map stores: key -> { value, expiryTime }
    this.cache = new Map();
  }

  /**
   * Check if an entry is expired based on its expiry time.
   */
  isExpired(expiryTime) {
    if (expiryTime === Infinity) {
      return false;
    }
    return this.now() >= expiryTime;
  }

  /**
   * Remove expired entries from the cache.
   */
  purgeExpired() {
    const keysToDelete = [];
    for (const [key, entry] of this.cache) {
      if (this.isExpired(entry.expiryTime)) {
        keysToDelete.push(key);
      }
    }
    for (const key of keysToDelete) {
      this.cache.delete(key);
    }
  }

  /**
   * Set a key-value pair with optional TTL.
   * Returns this for chaining.
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiryTime = ttl === Infinity ? Infinity : this.now() + ttl;

    // If key already exists, delete it first (to update recency)
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }

    // Purge expired entries
    this.purgeExpired();

    // If still over capacity, evict LRU (first entry in Map)
    while (this.cache.size >= this.capacity) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    // Insert the new entry at the end (most recently used)
    this.cache.set(key, { value, expiryTime });

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
    if (this.isExpired(entry.expiryTime)) {
      this.cache.delete(key);
      return undefined;
    }

    // Move to end (most recently used) by deleting and re-inserting
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
    if (this.isExpired(entry.expiryTime)) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete a key from the cache.
   * Returns true if something was deleted, false otherwise.
   */
  delete(key) {
    return this.cache.delete(key);
  }

  /**
   * Get the number of live (non-expired) entries.
   */
  get size() {
    this.purgeExpired();
    return this.cache.size;
  }

  /**
   * Get an array of live keys ordered from most recently used to least recently used.
   */
  keys() {
    this.purgeExpired();
    // Map iteration order is insertion order, so reverse to get MRU first
    return Array.from(this.cache.keys()).reverse();
  }
}
