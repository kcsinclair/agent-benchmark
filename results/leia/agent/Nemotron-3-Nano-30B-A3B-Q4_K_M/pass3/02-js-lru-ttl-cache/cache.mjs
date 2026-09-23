export class LruTtlCache {
  /**
   * @param {{capacity: number, defaultTtlMs?: number, now?: () => number}} options
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be a positive integer');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this._now = now;
    this.map = new Map(); // key => {value, expiry}
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs ?? this.defaultTtlMs;
    if (ttl <= 0) return this; // entry already expired – ignore

    const now = this._now();
    const expiry = ttl === Infinity ? Infinity : now + ttl;

    const existing = this.map.get(key);
    if (existing) {
      // Update existing entry
      existing.value = value;
      existing.expiry = expiry;
      // Move to most‑recent position
      this.map.delete(key);
      this.map.set(key, existing);
      return this;
    }

    // Need to insert a new entry – possibly evict
    while (this.map.size >= this.capacity) {
      // Look at the least‑recently used entry (first in iteration)
      const iterator = this.map.keys();
      const firstResult = iterator.next();
      if (firstResult.done) break;
      const firstKey = firstResult.value;
      const firstEntry = this.map.get(firstKey);

      // If it is expired, just delete it and continue
      if (firstEntry.expiry !== Infinity && now >= firstEntry.expiry) {
        this.map.delete(firstKey);
      } else {
        // Not expired – evict it to make space
        this.map.delete(firstKey);
        break;
      }
    }

    // After possible eviction, check again
    if (this.map.size >= this.capacity) {
      const lruKey = this.map.keys().next().value;
      if (lruKey) this.map.delete(lruKey);
    }

    // Insert the new entry (will be placed at the end → most recent)
    const newEntry = { value, expiry };
    this.map.set(key, newEntry);
    return this;
  }

  get(key) {
    const entry = this.map.get(key);
    if (!entry) return undefined;

    // Check expiration
    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this.map.delete(key);
      return undefined;
    }

    // Not expired – make it most recent
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.map.get(key);
    if (!entry) return false;
    if (entry.expiry !== Infinity && this._now() >= entry.expiry) {
      this.map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.map.delete(key);
  }

  get size() {
    // Purge expired entries first
    const now = this._now();
    const toDelete = [];
    for (const [k, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        toDelete.push(k);
      }
    }
    for (const k of toDelete) this.map.delete(k);
    return this.map.size;
  }

  keys() {
    // Remove expired entries
    const now = this._now();
    const toDelete = [];
    for (const [k, entry] of this.map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        toDelete.push(k);
      }
    }
    for (const k of toDelete) this.map.delete(k);

    // Collect remaining keys (oldest → newest) then reverse
    const keys = [];
    for (const [k] of this.map) {
      keys.push(k);
    }
    return keys.reverse(); // most recent first
  }
}
