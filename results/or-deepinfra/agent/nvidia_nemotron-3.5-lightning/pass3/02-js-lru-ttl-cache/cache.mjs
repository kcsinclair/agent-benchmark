export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("capacity must be an integer >= 1");
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key -> { value, expiry }
  }

  _expired(entry) {
    if (!entry) return true;
    const { expiry } = entry;
    if (expiry === Infinity) return false;
    return this.now() >= expiry;
  }

  _purgeExpired() {
    for (const [key, entry] of this.map) {
      if (this._expired(entry)) {
        this.map.delete(key);
      } else {
        // since Map is ordered, once we find a non-expired entry,
        // the rest are also non-expired (but not guaranteed by recency,
        // so we just continue scanning). We break to avoid O(n) every time,
        // but we still purge all expired ones on this pass.
        break;
      }
    }
    // Actually, we need to purge *all* expired entries, not just until the first non-expired.
    // Let's do a full scan.
    const keysToDelete = [];
    for (const [key, entry] of this.map) {
      if (this._expired(entry)) {
        keysToDelete.push(key);
      }
    }
    for (const key of keysToDelete) {
      this.map.delete(key);
    }
  }

  set(key, value, ttlMs) {
    this._purgeExpired();

    const expiry = ttlMs !== undefined && ttlMs !== null && ttlMs !== -Infinity
      ? (this.now() + ttlMs)
      : Infinity;

    // If key already exists, update value and expiry, and move to most recent
    if (this.map.has(key)) {
      const existing = this.map.get(key);
      // update entry
      this.map.set(key, { value, expiry });
      // Move to end (most recently used) - Map.prototype.set does this automatically
      return this;
    }

    // Insert new entry
    this.map.set(key, { value, expiry });

    // Evict if over capacity
    while (this.map.size > this.capacity) {
      // evict the least recently used (first entry in Map)
      const firstKey = this.map.keys().next().value;
      this.map.delete(firstKey);
    }

    return this;
  }

  get(key) {
    this._purgeExpired();

    if (!this.map.has(key)) {
      return undefined;
    }

    const entry = this.map.get(key);
    if (this._expired(entry)) {
      this.map.delete(key);
      return undefined;
    }

    // Move to end (most recently used)
    // Since we accessed it, we need to move it to the end.
    // Map does not have a move-to-end method, so we delete and re-insert.
    const { value, expiry } = entry;
    this.map.delete(key);
    this.map.set(key, { value, expiry });

    return value;
  }

  has(key) {
    this._purgeExpired();

    if (!this.map.has(key)) {
      return false;
    }

    const entry = this.map.get(key);
    if (this._expired(entry)) {
      this.map.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    this._purgeExpired();
    const existed = this.map.has(key);
    if (existed) {
      this.map.delete(key);
    }
    return existed;
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    // Return keys from most recently used to least recently used.
    // Map insertion order is oldest->newest, so we need to reverse.
    // However, we also have reordering via get/set which delete+reinsert.
    // So the current order is MRU at the end, LRU at the front.
    // We want most recent first, so we reverse the array.
    const arr = Array.from(this.map.keys()).reverse();
    return arr;
  }
}
