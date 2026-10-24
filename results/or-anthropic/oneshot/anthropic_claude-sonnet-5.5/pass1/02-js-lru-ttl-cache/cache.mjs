// cache.mjs
export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  // Map insertion order: first = least recently used, last = most recently used.
  #map = new Map(); // key -> { key, value, expiry }
  // Min-heap on expiry with lazy deletion (entries whose map record was replaced/removed are stale).
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
    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : t + ttl;

    this.#map.delete(key); // replaced entry becomes stale in the heap
    const entry = { key, value, expiry };
    this.#map.set(key, entry);
    if (expiry !== Infinity) this.#heapPush(entry);

    if (this.#map.size > this.#capacity) {
      this.#purgeExpired(t);
      while (this.#map.size > this.#capacity) {
        const lru = this.#map.keys().next().value;
        this.#map.delete(lru);
      }
    }
    this.#maybeCompact();
    return this;
  }

  get(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return undefined;
    if (this.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return undefined;
    }
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    const entry = this.#map.get(key);
    if (entry === undefined) return false;
    if (this.#isExpired(entry, this.#now())) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    this.#purgeExpired(this.#now());
    return this.#map.size;
  }

  keys() {
    this.#purgeExpired(this.#now());
    return Array.from(this.#map.keys()).reverse();
  }

  // ---- internals ----

  #isExpired(entry, t) {
    return entry.expiry !== Infinity && t >= entry.expiry;
  }

  #purgeExpired(t) {
    const heap = this.#heap;
    while (heap.length > 0) {
      const top = heap[0];
      if (this.#map.get(top.key) !== top) {
        this.#heapPop(); // stale
      } else if (this.#isExpired(top, t)) {
        this.#heapPop();
        this.#map.delete(top.key);
      } else {
        break;
      }
    }
  }

  #maybeCompact() {
    if (this.#heap.length <= 2 * this.#map.size + 16) return;
    this.#heap = this.#heap.filter((e) => this.#map.get(e.key) === e);
    for (let i = (this.#heap.length >> 1) - 1; i >= 0; i--) this.#siftDown(i);
  }

  #heapPush(entry) {
    const h = this.#heap;
    h.push(entry);
    let i = h.length - 1;
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
    if (h.length > 0) {
      h[0] = last;
      this.#siftDown(0);
    }
  }

  #siftDown(i) {
    const h = this.#heap;
    const n = h.length;
    for (;;) {
      let s = i;
      const l = 2 * i + 1;
      const r = l + 1;
      if (l < n && h[l].expiry < h[s].expiry) s = l;
      if (r < n && h[r].expiry < h[s].expiry) s = r;
      if (s === i) break;
      [h[s], h[i]] = [h[i], h[s]];
      i = s;
    }
  }
}
