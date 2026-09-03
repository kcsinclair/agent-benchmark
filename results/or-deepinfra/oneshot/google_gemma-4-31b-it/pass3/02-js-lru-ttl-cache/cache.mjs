/**
 * LruTtlCache implements a Least Recently Used (LRU) cache with 
 * Time-To-Live (TTL) expiration.
 */
export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('Capacity must be an integer >= 1');
    }

    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    
    // Map preserves insertion order. 
    // In this implementation, the "most recently used" item is the one 
    // most recently inserted/updated in the Map.
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
   * Internal helper to remove an entry and return true.
   */
  _remove(key) {
    return this._cache.delete(key);
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = this._now() + ttl;

    // If key exists, remove it first to update position to "most recent"
    if (this._cache.has(key)) {
      this._cache.delete(key);
    }

    // Evict if we are at capacity
    if (this._cache.size >= this._capacity) {
      this._evict();
    }

    this._cache.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this._cache.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry.expiry)) {
      this._remove(key);
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
      this._remove(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this._remove(key);
  }

  /**
   * Evicts expired entries first. If still over capacity, evicts the LRU entry.
   */
  _evict() {
    // 1. Try to find any expired entry to evict first
    for (const [key, entry] of this._cache.entries()) {
      if (this._isExpired(entry.expiry)) {
        this._remove(key);
        return; // Evicted one expired item, capacity is now available
      }
    }

    // 2. If no expired entries, evict the oldest (first entry in Map)
    const oldestKey = this._cache.keys().next().value;
    if (oldestKey !== undefined) {
      this._remove(oldestKey);
    }
  }

  get size() {
    // We must purge expired entries to return the count of "live" entries
    for (const [key, entry] of this._cache.entries()) {
      if (this._isExpired(entry.expiry)) {
        this._remove(key);
      }
    }
    return this._cache.size;
  }

  keys() {
    const liveKeys = [];
    // Map iterates in insertion order (oldest to newest).
    // We need most recently used to least recently used (newest to oldest).
    const allKeys = Array.from(this._cache.keys());
    
    // Filter out expired keys and reverse the order
    for (let i = allKeys.length - 1; i >= 0; i--) {
      const key = allKeys[i];
      const entry = this._cache.get(key);
      if (entry && !this._isExpired(entry.expiry)) {
        liveKeys.push(key);
      } else if (entry) {
        this._remove(key); // Clean up expired entry discovered during keys()
      }
    }
    
    return liveKeys;
  }
}
