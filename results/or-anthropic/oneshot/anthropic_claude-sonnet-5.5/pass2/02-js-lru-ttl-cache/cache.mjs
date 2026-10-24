// cache.mjs
export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map insertion order: first = least recently used, last = most recently used.
  #map = new Map();
  // Min-heap (by expiry) of entries with finite expiry. Removed entries are
  // flagged `dead` and discarded lazily when they reach the top (or on compaction).
  #heap = [];

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  set(key, value, ttlMs) {
    const t = this.#now();
    const existing = this.#map.get(key);
    if (existing) this.#remove(existing);

    const expiry = t + (ttlMs ?? this.#defaultTtlMs);
    const entry = { key, value, expiry, dead: false };
    this.#map.set(key, entry);
    if (expiry !== Infinity) this.#heapPush(entry);

    if (this.#map.size > this.#capacity) {
      this.#purgeExpired(t); // expired entries go first
      while (this.#map.size > this.#capacity) {
        const lru = this.#map.values().next().value;
        this.#remove(lru);
      }
    }
    this.#maybeCompact();
    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (!entry) return undefined;
    if (this.#isExpired(entry, this.#now())) {
      this.#remove(entry);
      return undefined;
    }
    // Move to most-recently-used position.
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (!entry) return false;
    if (this.#isExpired(entry, this.#now())) {
      this.#remove(entry);
      return false;
    }
    return true;
  }

  delete(key) {
    const entry = this.#map.get(key);
    if (!entry) return false;
    const expired = this.#isExpired(entry, this.#now());
    this.#remove(entry);
    return !expired; // an already-expired entry was logically gone
  }

  get size() {
    this.#purgeExpired(this.#now());
    return this.#map.size;
  }

  keys() {
    this.#purgeExpired(this.#now());
    return [...this.#map.keys()].reverse();
  }

  // ---- internals ----

  #isExpired(entry, t) {
    return entry.expiry !== Infinity && t >= entry.expiry;
  }

  #remove(entry) {
    entry.dead = true;
    this.#map.delete(entry.key);
  }

  #purgeExpired(t) {
    const heap = this.#heap;
    while (heap.length > 0) {
      const top = heap[0];
      if (top.dead) {
        this.#heapPop();
      } else if (t >= top.expiry) {
        this.#heapPop();
        this.#remove(top);
      } else {
        break;
      }
    }
  }

  #maybeCompact() {
    if (this.#heap.length <= 2 * this.#capacity + 32) return;
    const live = this.#heap.filter((e) => !e.dead);
    this.#heap = [];
    for (const e of live) this.#heapPush(e);
  }

  #heapPush(entry) {
    const h = this.#heap;
    let i = h.length;
    h.push(entry);
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (h[p].expiry <= h[i].expiry) break;
      [h[p], h[i]] = [h[i], h[p]];
      i = p;
    }
  }

  #heapPop() {
    const h = this.#heap;
    const last = h.pop();
    if (h.length === 0) return;
    h[0] = last;
    let i = 0;
    const n = h.length;
    for (;;) {
      const l = 2 * i + 1;
      const r = l + 1;
      let m = i;
      if (l < n && h[l].expiry < h[m].expiry) m = l;
      if (r < n && h[r].expiry < h[m].expiry) m = r;
      if (m === i) break;
      [h[m], h[i]] = [h[i], h[m]];
      i = m;
    }
  }
}
