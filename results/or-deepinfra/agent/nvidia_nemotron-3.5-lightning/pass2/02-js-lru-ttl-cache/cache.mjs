export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("capacity must be an integer >= 1");
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key -> { value, expiry }
    this.lru = new Map(); // key -> position (order), we use Map insertion order for LRU
  }

  set(key, value, ttlMs) {
    const now = this.now();
    const expiry = ttlMs === undefined
      ? this.defaultTtlMs === Infinity ? Infinity : this.now() + this.defaultTtlMs
      : ttlMs === Infinity ? Infinity : now + ttlMs;

    // If ttlMs is 0 or negative, entry is already expired
    // But we still insert it; expiry will be in the past.

    const entry = { value, expiry };

    // If key already exists, update value and expiry, move to most recent
    if (this.map.has(key)) {
      this.map.set(key, entry);
      // Move to end in lru Map (by deleting and re-adding)
      this.lru.delete(key);
      this.lru.set(key, true);
      // Ensure size does not exceed capacity after update (it shouldn't grow)
      return this;
    }

    // Insert new entry
    this.map.set(key, entry);
    this.lru.set(key, true);

    // Evict if over capacity
    this._trim();

    return this;
  }

  get(key) {
    if (!this.map.has(key)) return undefined;

    const entry = this.map.get(key);
    const now = this.now();

    // Check expiry
    if (entry.expiry !== Infinity && now >= entry.expiry) {
      // Expired, remove from both maps
      this.map.delete(key);
      this.lru.delete(key);
      return undefined;
    }

    // Move to most recently used
    this.lru.delete(key);
    this.lru.set(key, true);

    return entry.value;
  }

  has(key) {
    if (!this.map.has(key)) return false;

    const entry = this.map.get(key);
    const now = this.now();

    if (entry.expiry !== Infinity && now >= entry.expiry) {
      // Expired, remove
      this.map.delete(key);
      this.lru.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    if (this.map.has(key)) {
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
    // Return keys in LRU order: most recently used to least
    // Since this.lru maintains insertion order (last added = most recent),
    // we need to reverse or iterate appropriately.
    // We built lru by re-adding on access, so the order from first to last is least recent to most recent.
    // Actually, let's think: when we set or get, we delete and re-add to lru.
    // So the lru Map order is: oldest -> newest.
    // We want newest -> oldest.
    const arr = Array.from(this.lru.keys()).reverse();
    return arr.filter(k => this.map.has(k)); // filter may remove expired after purge
  }

  _purgeExpired() {
    const now = this.now();
    const toDelete = [];
    for (const [key, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        toDelete.push(key);
      }
    }
    for (const key of toDelete) {
      this.map.delete(key);
      this.lru.delete(key);
    }
  }

  _trim() {
    // Purge expired first
    this._purgeExpired();

    // If still over capacity, evict LRU entries
    while (this.map.size > this.capacity) {
      // The first key in lru is the least recently used
      const lruKey = this.lru.keys().next().value;
      if (lruKey === undefined) break;
      this.map.delete(lruKey);
      this.lru.delete(lruKey);
    }
  }
}
