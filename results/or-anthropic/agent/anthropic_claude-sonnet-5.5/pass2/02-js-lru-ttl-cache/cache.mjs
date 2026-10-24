export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #map = new Map(); // key -> { value, expiry }; insertion order = LRU -> MRU
  #minExpiry = Infinity; // lower bound on the earliest expiry among entries

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
  }

  #isExpired(entry, t) {
    return entry.expiry !== Infinity && t >= entry.expiry;
  }

  #purge() {
    const t = this.#now();
    if (t < this.#minExpiry) return;
    let min = Infinity;
    for (const [k, e] of this.#map) {
      if (this.#isExpired(e, t)) this.#map.delete(k);
      else if (e.expiry < min) min = e.expiry;
    }
    this.#minExpiry = min;
  }

  set(key, value, ttlMs) {
    const t = this.#now();
    const ttl = ttlMs ?? this.#defaultTtlMs;
    const expiry = ttl === Infinity ? Infinity : t + ttl;
    const existed = this.#map.delete(key);
    if (expiry !== Infinity && t >= expiry) {
      // already expired: replaces (removes) any existing entry, stores nothing
      return this;
    }
    if (!existed && this.#map.size >= this.#capacity) {
      this.#purge();
      while (this.#map.size >= this.#capacity) {
        const oldest = this.#map.keys().next().value;
        this.#map.delete(oldest);
      }
    }
    this.#map.set(key, { value, expiry });
    if (expiry < this.#minExpiry) this.#minExpiry = expiry;
    return this;
  }

  get(key) {
    const e = this.#map.get(key);
    if (e === undefined) return undefined;
    if (this.#isExpired(e, this.#now())) {
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
    if (this.#isExpired(e, this.#now())) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    const e = this.#map.get(key);
    if (e === undefined) return false;
    this.#map.delete(key);
    // an expired entry counts as already gone
    return !this.#isExpired(e, this.#now());
  }

  get size() {
    this.#purge();
    return this.#map.size;
  }

  keys() {
    this.#purge();
    return Array.from(this.#map.keys()).reverse();
  }
}
