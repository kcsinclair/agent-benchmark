export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #map = new Map(); // key -> { value, expiry }; first = LRU, last = MRU

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  #expired(entry, t) {
    return entry.expiry !== Infinity && t >= entry.expiry;
  }

  #purge(t) {
    for (const [k, e] of this.#map) {
      if (this.#expired(e, t)) this.#map.delete(k);
    }
  }

  set(key, value, ttlMs) {
    const t = this.#now();
    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : t + ttl;
    this.#map.delete(key);
    if (expiry !== Infinity && t >= expiry) return this; // already expired
    if (this.#map.size >= this.#capacity) {
      this.#purge(t);
      while (this.#map.size >= this.#capacity) {
        this.#map.delete(this.#map.keys().next().value);
      }
    }
    this.#map.set(key, { value, expiry });
    return this;
  }

  get(key) {
    const e = this.#map.get(key);
    if (e === undefined) return undefined;
    if (this.#expired(e, this.#now())) {
      this.#map.delete(key);
      return undefined;
    }
    this.#map.delete(key);
    this.#map.set(key, e);
    return e.value;
  }

  has(key) {
    const e = this.#map.get(key);
    if (e === undefined) return false;
    if (this.#expired(e, this.#now())) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    this.#purge(this.#now());
    return this.#map.size;
  }

  keys() {
    this.#purge(this.#now());
    return [...this.#map.keys()].reverse();
  }
}
