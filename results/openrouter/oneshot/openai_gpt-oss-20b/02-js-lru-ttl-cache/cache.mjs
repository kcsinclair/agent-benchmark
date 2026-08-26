// cache.mjs
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key → { value, expiry }
  }

  /* internal helper – true if the entry is expired */
  _isExpired(entry) {
    return entry.expiry !== Infinity && this.now() >= entry.expiry;
  }

  /** Insert or replace a key/value pair.
   *  The entry expires at now() + ttlMs (or defaultTtlMs if omitted).
   *  The key becomes the most‑recently used entry.
   *  Evicts expired entries first, then LRU if capacity is exceeded. */
  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this.defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this.now() + ttl;

    // Update order: delete first if key already exists
    if (this.map.has(key)) this.map.delete(key);
    this.map.set(key, { value, expiry });

    // Evict until we are within capacity
    while (this.map.size > this.capacity) {
      const firstKey = this.map.keys().next().value;
      const firstEntry = this.map.get(firstKey);
      if (this._isExpired(firstEntry)) {
        this.map.delete(firstKey);
        continue; // keep evicting expired entries
      }
      // Evict least‑recently used
      this.map.delete(firstKey);
      break;
    }
    return this;
  }

  /** Retrieve a value by key.
   *  Returns undefined if the key is missing or expired.
   *  A hit makes the entry most‑recently used. */
  get(key) {
    const entry = this.map.get(key);
    if (!entry) return undefined;
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return undefined;
    }
    // Move to the end (most‑recent)
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  /** Check if a key is present and not expired.
   *  Does not affect recency. */
  has(key) {
    const entry = this.map.get(key);
    if (!entry) return false;
    if (this._isExpired(entry)) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  /** Remove a key. Returns true if something was removed. */
  delete(key) {
    return this.map.delete(key);
  }

  /** Number of live (non‑expired) entries. Purges expired ones. */
  get size() {
    const now = this.now();
    for (const [key, entry] of this.map.entries()) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
      }
    }
    return this.map.size;
  }

  /** Array of live keys from most‑recently used to least‑recently used. */
  keys() {
    const now = this.now();
    const live = [];
    for (const [key, entry] of this.map.entries()) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this.map.delete(key);
        continue;
      }
      live.push(key);
    }
    return live.reverse(); // reverse to get MRU → LRU
  }
}
