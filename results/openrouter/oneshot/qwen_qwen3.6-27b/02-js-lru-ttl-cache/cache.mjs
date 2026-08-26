export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    // Map preserves insertion order. We move entries to the end on access.
    // Entries are stored as { value, expiry }
    this.map = new Map();
  }

  /**
   * Internal helper to check if an entry is expired.
   * @param {number} expiry
   * @returns {boolean}
   */
  _isExpired(expiry) {
    if (expiry === Infinity) return false;
    return this.now() >= expiry;
  }

  /**
   * Internal helper to remove an entry from the map.
   * @param {any} key
   * @returns {boolean} true if the key existed and was removed.
   */
  _remove(key) {
    return this.map.delete(key);
  }

  /**
   * Internal helper to get an entry without updating recency, checking expiry.
   * @param {any} key
   * @returns {{ value: any, expiry: number } | null}
   */
  _getEntry(key) {
    const entry = this.map.get(key);
    if (entry === undefined) return null;
    if (this._isExpired(entry.expiry)) {
      this._remove(key);
      return null;
    }
    return entry;
  }

  /**
   * Internal helper to evict expired entries first, then LRU entries if needed.
   * @param {number} neededSpace - number of slots to free up.
   */
  _evict(neededSpace) {
    let freed = 0;
    // First pass: remove expired entries
    for (const [key, entry] of this.map) {
      if (this._isExpired(entry.expiry)) {
        this._remove(key);
        freed++;
        if (freed >= neededSpace) return;
      }
    }
    // Second pass: remove LRU entries (beginning of the map)
    while (this.map.size > this.capacity - neededSpace + freed) {
      // The first key in the map is the least recently used
      const firstKey = this.map.keys().next().value;
      if (firstKey === undefined) break;
      this._remove(firstKey);
    }
  }

  set(key, value, ttlMs) {
    const effectiveTtl = ttlMs ?? this.defaultTtlMs;
    const expiry = effectiveTtl === Infinity ? Infinity : this.now() + effectiveTtl;

    // If key exists, update it and move to end (most recently used)
    if (this.map.has(key)) {
      this.map.set(key, { value, expiry });
      this.map.delete(key); // Remove from current position
      this.map.set(key, { value, expiry }); // Re-add to end
      return this;
    }

    // If adding new key would exceed capacity, evict
    if (this.map.size >= this.capacity) {
      this._evict(1);
    }

    this.map.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const entry = this._getEntry(key);
    if (entry === null) return undefined;

    // Move to end (most recently used)
    this.map.delete(key);
    this.map.set(key, entry);

    return entry.value;
  }

  has(key) {
    const entry = this._getEntry(key);
    return entry !== null;
  }

  delete(key) {
    // Check if key exists and is not expired
    const entry = this.map.get(key);
    if (entry === undefined) return false;
    
    // If expired, remove it and return true (since we removed something)
    if (this._isExpired(entry.expiry)) {
      this._remove(key);
      return true;
    }
    
    // If not expired, remove it
    this._remove(key);
    return true;
  }

  get size() {
    // Purge expired entries and count live ones
    let count = 0;
    for (const [key, entry] of this.map) {
      if (this._isExpired(entry.expiry)) {
        this._remove(key);
      } else {
        count++;
      }
    }
    return count;
  }

  keys() {
    // Purge expired entries first
    for (const [key, entry] of this.map) {
      if (this._isExpired(entry.expiry)) {
        this._remove(key);
      }
    }
    // Map iteration order is insertion order, which we maintain as LRU order
    // (least recently used at the beginning, most recently used at the end)
    // We need most recently used first, so reverse the keys
    return [...this.map.keys()].reverse();
  }
}
