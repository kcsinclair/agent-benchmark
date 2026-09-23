export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map preserves insertion order; we use it for LRU ordering.
    // Each entry: { value, expiry }
    this._map = new Map();
  }

  get size() {
    // Purge expired entries and return count of live entries
    this._purgeExpired();
    return this._map.size;
  }

  _purgeExpired() {
    const now = this._now();
    const toDelete = [];
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        toDelete.push(key);
      }
    }
    for (const key of toDelete) {
      this._map.delete(key);
    }
  }

  _isExpired(entry) {
    if (entry.expiry === Infinity) return false;
    return this._now() >= entry.expiry;
  }

  _moveToMostRecent(key) {
    // Remove and re-insert to move to end (most recently used)
    const entry = this._map.get(key);
    if (entry !== undefined) {
      this._map.delete(key);
      this._map.set(key, entry);
    }
  }

  set(key, value, ttlMs) {
    const ttl = ttlMs !== undefined ? ttlMs : this._defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : this._now() + ttl;

    // If key already exists, remove it first (to re-insert at end)
    if (this._map.has(key)) {
      this._map.delete(key);
    }

    // Insert new entry at the end (most recently used)
    this._map.set(key, { value, expiry });

    // If over capacity, evict
    while (this._map.size > this._capacity) {
      // First, try to evict expired entries
      let evictedExpired = false;
      for (const [k, entry] of this._map) {
        if (this._isExpired(entry)) {
          this._map.delete(k);
          evictedExpired = true;
          break;
        }
      }
      if (evictedExpired) {
        continue;
      }
      // No expired entries to evict; evict least recently used (first in map)
      const firstKey = this._map.keys().next().value;
      this._map.delete(firstKey);
    }

    return this;
  }

  get(key) {
    const entry = this._map.get(key);
    if (entry === undefined) {
      return undefined;
    }
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return undefined;
    }
    // Move to most recently used
    this._moveToMostRecent(key);
    return entry.value;
  }

  has(key) {
    const entry = this._map.get(key);
    if (entry === undefined) {
      return false;
    }
    if (this._isExpired(entry)) {
      this._map.delete(key);
      return false;
    }
    // Does NOT affect recency
    return true;
  }

  delete(key) {
    const entry = this._map.get(key);
    if (entry === undefined) {
      return false;
    }
    this._map.delete(key);
    return true;
  }

  keys() {
    // Return live keys ordered from most recently used to least recently used
    // Map iteration order is insertion order (least recent first)
    // So we need to reverse
    const liveKeys = [];
    const now = this._now();
    const toDelete = [];
    for (const [key, entry] of this._map) {
      if (entry.expiry !== Infinity && now >= entry.expiry) {
        toDelete.push(key);
      } else {
        liveKeys.push(key);
      }
    }
    for (const key of toDelete) {
      this._map.delete(key);
    }
    // liveKeys is in LRU order (least recent first), reverse for MRU first
    return liveKeys.reverse();
  }
}
