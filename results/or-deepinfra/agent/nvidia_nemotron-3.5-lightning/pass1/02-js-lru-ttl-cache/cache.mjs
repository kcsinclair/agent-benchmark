export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("capacity must be an integer >= 1");
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key -> { value, expiry }
    this.lru = new Map(); // key -> value (insertion order = recency, most recent last)
  }

  _expired(expiry) {
    if (expiry === Infinity) return false;
    if (expiry <= 0) return true;
    return this.now() >= expiry;
  }

  _purgeExpired() {
    // Remove expired entries from both maps
    for (const [key, entry] of this.map) {
      if (this._expired(entry.expiry)) {
        this.map.delete(key);
        this.lru.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    const expiry = ttlMs !== undefined ? this.now() + ttlMs : this.now() + this.defaultTtlMs;

    // If key already exists, update value and expiry, move to most recent
    if (this.map.has(key)) {
      const oldExpiry = this.map.get(key).expiry;
      // If old entry was expired, we still need to update it; but we also need to remove it from lru to re-add
      this.map.set(key, { value, expiry });
      // Move to end of lru (most recently used)
      if (this.lru.has(key)) {
        this.lru.delete(key);
      }
      this.lru.set(key, value);
      return this;
    }

    // Purge expired entries first if we are at capacity
    // We may need to evict to make room
    while (this.map.size >= this.capacity) {
      // Evict expired entries first
      this._purgeExpired();
      if (this.map.size >= this.capacity) {
        // Still over capacity, evict LRU (first key in lru)
        const lruKey = this.lru.keys().next().value;
        this.lru.delete(lruKey);
        this.map.delete(lruKey);
      }
    }

    // Insert new entry
    this.map.set(key, { value, expiry });
    this.lru.set(key, value); // insertion order: most recent at end
    return this;
  }

  get(key) {
    if (!this.map.has(key)) return undefined;
    const entry = this.map.get(key);
    if (this._expired(entry.expiry)) {
      this.map.delete(key);
      this.lru.delete(key);
      return undefined;
    }
    // Move to most recently used: update lru order
    if (this.lru.has(key)) {
      this.lru.delete(key);
    }
    this.lru.set(key, entry.value);
    return entry.value;
  }

  has(key) {
    if (!this.map.has(key)) return false;
    const entry = this.map.get(key);
    if (this._expired(entry.expiry)) {
      this.map.delete(key);
      this.lru.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    const removed = this.map.has(key) && !this._expired(this.map.get(key).expiry);
    // Actually, we should just remove if key exists and not expired, but spec says returns true if something was removed
    // Let's handle properly:
    if (this.map.has(key)) {
      const entry = this.map.get(key);
      if (this._expired(entry.expiry)) {
        this.map.delete(key);
        this.lru.delete(key);
        return false;
      }
      this.map.delete(key);
      this.lru.delete(key);
      return true;
    }
    return false;
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    // Return keys in MRU to LRU order. lru insertion order: first is LRU, last is MRU.
    // We want MRU first, so reverse.
    const keys = Array.from(this.lru.keys()).reverse();
    return keys;
  }
}
