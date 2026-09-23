// cache.mjs
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    this._map = new Map(); // key -> { value, expiry }
  }

  set(key, value, ttlMs) {
    const now = this._now();
    const ttl = ttlMs ?? this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : now + ttl;

    // If key exists, update value and expiry, move to front (most recently used)
    if (this._map.has(key)) {
      const entry = this._map.get(key);
      entry.value = value;
      entry.expiry = expiry;
      this._map.delete(key);
      this._map.set(key, entry);
      return this;
    }

    // Insert new entry
    this._map.set(key, { value, expiry });

    // Eviction logic: first purge expired entries, then evict LRU if still over capacity
    this._purgeExpired();

    while (this._map.size > this._capacity) {
      // Map preserves insertion order; first entry is least recently used
      const firstKey = this._map.keys().next().value;
      this._map.delete(firstKey);
    }

    return this;
  }

  get(key) {
    if (!this._map.has(key)) return undefined;

    const entry = this._map.get(key);
    const now = this._now();

    // Check expiry
    if (entry.expiry !== Infinity && now >= entry.expiry) {
      this._map.delete(key);
      return undefined;
    }

    // Move to front (most recently used) by re-inserting
    this._map.delete(key);
    this._map.set(key, entry);

    return entry.value;
  }

  has(key) {
    if (!this._map.has(key)) return false;

    const entry = this._map.get(key);
    const now = this._now();

    if (entry.expiry !== Infinity && now >= entry.expiry) {
      this._map.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this._map.delete(key);
  }

  // Getter: number of live (non-expired) entries, purging expired ones
  get size() {
    this._purgeExpired();
    return this._map.size;
  }

  // Array of live keys ordered from most recently used to least recently used
  keys() {
    this._purgeExpired();
    // Map iteration order is insertion order; we moved entries to front on get/set,
    // so the last entries are the most recently used. Reverse to get MRU first.
    return Array.from(this._map.keys()).reverse();
  }

  // Internal: remove all entries that are expired according to current clock
  _purgeExpired() {
    const now = this._now();
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        this._map.delete(key);
      }
    }
  }
}
