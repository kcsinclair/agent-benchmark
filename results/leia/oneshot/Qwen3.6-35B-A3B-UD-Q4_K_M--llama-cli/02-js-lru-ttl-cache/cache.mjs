/**
 * LRU cache with per-entry time-to-live.
 *
 * All time arithmetic goes through the injected `now` clock.
 */
export class LruTtlCache {
  /**
   * @param {object} options
   * @param {number} options.capacity         Integer ≥ 1.
   * @param {number} [options.defaultTtlMs]   Default TTL per entry (ms). Default `Infinity`.
   * @param {function(): number} [options.now] Clock function returning epoch ms.
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError("capacity must be an integer ≥ 1");
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;
    // Map keeps insertion order → MRU-first when we re-insert on access.
    this._store = new Map();
  }

  // ── helpers ──────────────────────────────────────────────────────────

  /** Resolve the effective expiry for a set call. */
  _expiry(ttlMs) {
    const effective = ttlMs ?? this._defaultTtlMs;
    return effective === Infinity ? Infinity : this._now() + effective;
  }

  /** Return `true` if `expiry` represents an expired entry at current time. */
  _isExpired(expiry) {
    return expiry !== Infinity && this._now() >= expiry;
  }

  /** Delete a key from the internal map; return `true` if it existed. */
  _rawDelete(key) {
    if (this._store.has(key)) {
      this._store.delete(key);
      return true;
    }
    return false;
  }

  // ── public API ───────────────────────────────────────────────────────

  /** Insert or update an entry. Returns `this` for chaining. */
  set(key, value, ttlMs) {
    const expiry = this._expiry(ttlMs);

    // If the key already exists, update value + expiry in-place and
    // "refresh" recency by deleting and re-inserting so it lands at the
    // end of the Map (most-recently-used).
    if (this._store.has(key)) {
      this._store.delete(key);
      this._store.set(key, { value, expiry });
    } else {
      this._store.set(key, { value, expiry });

      // Evict if over capacity.
      while (this._store.size > this._capacity) {
        // Evict expired entries first (iterate LRU → MRU = front → end).
        let evicted = false;
        for (const [k, entry] of this._store) {
          if (this._isExpired(entry.expiry)) {
            this._store.delete(k);
            evicted = true;
            break;
          }
        }
        if (!evicted) {
          // No expired entries — evict the LRU (first in iteration order).
          const lruKey = this._store.keys().next().value;
          this._store.delete(lruKey);
        }
      }
    }
    return this;
  }

  /** Retrieve a value by key. Returns `undefined` if absent or expired. */
  get(key) {
    const entry = this._store.get(key);
    if (!entry) return undefined;

    if (this._isExpired(entry.expiry)) {
      this._store.delete(key);
      return undefined;
    }

    // Bump to MRU: delete and re-insert.
    this._store.delete(key);
    this._store.set(key, entry);
    return entry.value;
  }

  /** Check if a key exists and is not expired. Does not affect recency. */
  has(key) {
    const entry = this._store.get(key);
    if (!entry) return false;

    if (this._isExpired(entry.expiry)) {
      this._store.delete(key);
      return false;
    }

    return true;
  }

  /** Delete a key. Returns `true` if the key was present. */
  delete(key) {
    return this._rawDelete(key);
  }

  /** Number of live (non-expired) entries. Purges expired on read. */
  get size() {
    // Purge expired entries; iterate from LRU → MRU (reverse).
    const keys = [...this._store.keys()];
    for (let i = keys.length - 1; i >= 0; i--) {
      const key = keys[i];
      const entry = this._store.get(key);
      if (this._isExpired(entry.expiry)) {
        this._store.delete(key);
      }
    }
    return this._store.size;
  }

  /** Live keys ordered MRU → LRU. */
  keys() {
    // Purge expired first.
    const toDelete = [];
    for (const [key, entry] of this._store) {
      if (this._isExpired(entry.expiry)) {
        toDelete.push(key);
      }
    }
    for (const key of toDelete) {
      this._store.delete(key);
    }
    // Map iteration order is insertion order; we re-insert on get/set
    // so MRU entries appear at the end. Return reversed for MRU-first.
    return [...this._store.keys()].reverse();
  }
}
