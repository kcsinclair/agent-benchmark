/**
 * LruTtlCache implements a Least Recently Used (LRU) cache 
 * with Time-To-Live (TTL) expiration.
 */
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer >= 1');
    }

    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    
    // Map in JS preserves insertion order. 
    // We treat the "end" of the map as the Most Recently Used (MRU).
    this._cache = new Map();
  }

  /**
   * Internal helper to check if an entry is expired.
   */
  _isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this._now() >= expiry;
  }

  /**
   * Internal helper to remove expired entries to free up space.
   * Since we don't have a priority queue for TTLs, we check 
   * the oldest entries (LRU) first, but we must be careful 
   * as TTLs are not necessarily correlated with recency.
   * However, the requirement says "evict expired entries first" 
   * when over capacity.
   */
  _purgeExpired() {
    const currentTime = this._now();
    for (const [key, entry] of this._cache.entries()) {
      if (entry.expiry !== Infinity && currentTime >= entry.expiry) {
        this._cache.delete(key);
      }
    }
  }

  set(key, value, ttlMs) {
    // If key exists, remove it first to update position to MRU
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    const expiry = this._now() + (ttlMs !== undefined ? ttlMs : this._defaultTtlMs);
    
    // If we are at capacity, we must make room
    if (this._cache.size >= this._capacity) {
      // 1. Try to evict any expired entries first
      this._purgeExpired();
      
      // 2. If still over capacity, evict the Least Recently Used (first key in Map)
      if (this._cache.size >= this._capacity) {
        const firstKey = this._cache.keys().next().value;
        this._cache.delete(firstKey);
      }
    }

    this._cache.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry.expiry)) {
      this._cache.delete(key);
      return undefined;
    }

    // Refresh recency: delete and re-insert
    this._cache.delete(key);
    this._cache.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this._cache.get(key);
    if (!entry) return false;

    if (this._isExpired(entry.expiry)) {
      this._cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this._cache.delete(key);
  }

  get size() {
    // Must purge expired entries to return accurate live count
    this._purgeExpired();
    return this._cache.size;
  }

  keys() {
    // Purge expired entries first
    this._purgeExpired();
    // Map keys are LRU -> MRU. Requirement asks for MRU -> LRU.
    return Array.from(this._cache.keys()).reverse();
  }
}
