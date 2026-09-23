export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #map;

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() } = {}) {
    if (typeof capacity !== 'number' || !Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }
    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#map = new Map();
  }

  #isExpired(entry, currentTime) {
    if (entry.expiry === Infinity) return false;
    return currentTime >= entry.expiry;
  }

  set(key, value, ttlMs) {
    const effectiveTtl = ttlMs ?? this.#defaultTtlMs;
    const currentTime = this.#now();

    const expiry = effectiveTtl === Infinity ? Infinity : currentTime + effectiveTtl;

    if (this.#isExpired({ expiry }, currentTime)) {
      this.#map.delete(key);
      return this;
    }

    if (this.#map.has(key)) {
      this.#map.delete(key);
    } else if (this.#map.size >= this.#capacity) {
      for (const [k, entry] of this.#map) {
        if (this.#isExpired(entry, currentTime)) {
          this.#map.delete(k);
        }
      }

      if (this.#map.size >= this.#capacity) {
        const lruKey = this.#map.keys().next().value;
        this.#map.delete(lruKey);
      }
    }

    this.#map.set(key, { value, expiry });
    return this;
  }

  get(key) {
    if (!this.#map.has(key)) {
      return undefined;
    }
    const entry = this.#map.get(key);
    const currentTime = this.#now();
    if (this.#isExpired(entry, currentTime)) {
      this.#map.delete(key);
      return undefined;
    }
    this.#map.delete(key);
    this.#map.set(key, entry);
    return entry.value;
  }

  has(key) {
    if (!this.#map.has(key)) {
      return false;
    }
    const entry = this.#map.get(key);
    const currentTime = this.#now();
    if (this.#isExpired(entry, currentTime)) {
      this.#map.delete(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#map.delete(key);
  }

  get size() {
    const currentTime = this.#now();
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry, currentTime)) {
        this.#map.delete(k);
      }
    }
    return this.#map.size;
  }

  keys() {
    const currentTime = this.#now();
    const result = [];
    for (const [k, entry] of this.#map) {
      if (this.#isExpired(entry, currentTime)) {
        this.#map.delete(k);
      } else {
        result.push(k);
      }
    }
    return result.reverse();
  }
}
