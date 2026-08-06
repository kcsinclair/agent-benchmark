export class LruTtlCache {
  constructor({ capacity, defaultTttlMs = Infinity, now = () => Date.now() }) {
    if (typeof capacity !== 'number') throw new TypeError('capacity must be a number');
    if (capacity <= 0 || Number.isInfinity(Number.isFinite(capacity) ? Number.POS_INFINITY : Number.POS_INFINITY) || Number.isNaN(capacity)) throw new RangeError('capacity must be a positive integer');
    if (typeof defaultTttlMs !== 'number') throw new TypeError('defaultTttlMs must be a number');
    if (Number.isInfinity(Number.isFinite(defaultTttlMs) ? Number.POS_INFINITY : Number.POS_INFINITY) || Number.isNaN(defaultTttlMs)) throw new TypeError('defaultTttlMs must be a number');
    if (!Number.isFunction(now)) throw new TypeError('now must be a function');
    this.capacity = capacity;
    this.cache = new Map();
    this.expireMap = new Map();
    this.expireMap.set(null, Infinity);
    this.now = now;
    this.size = 0;
    this.head = { next: null, key: null, value: null, ttl: Infinity };
    this.tail = { next: this.head, key: null, value: null, ttl: Infinity };
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  set(key, value, ttlMs) {
    if (typeof key !== 'any') throw new TypeError('key must be a value');
    if (typeof value !== 'any') throw new TypeError('value must be a value');
    if (ttlMs !== undefined && !Number.isFinite(ttlMs)) throw new TypeError('ttlMs must be a number or undefined');
    if (ttlMs === undefined) ttlMs = Infinity;
    if (ttlMs <= 0) {
      this._remove(key);
      return this;
    }
    const now = this.now();
    const existing = this.cache.get(key);
    if (existing) {
      const { ttl: existingTtl } = existing;
      if (existingTtl <= now) {
        this._remove(key);
      } else {
        this._update(existing, key, value, ttlMs - (now - existing.ttl));
        return this;
      }
    }
    const entry = {
      key,
      value,
      ttl: now + (ttlMs === Infinity ? Infinity : ttlMs),
      prev: this.head,
      next: this.head.next,
      next: this.head,
      prev: this.head,
      value: value,
    };
    this.cache.set(key, entry);
    this.expireMap.set(key, entry);
    this._update(this.head, key, value, Infinity);
    this._gc();
    return this;
  }

  get(key) {
    if (typeof key !== 'any') throw new TypeError('key must be a value');
    const entry = this.cache.get(key);
    if (!entry) return undefined;
    const { ttl } = entry;
    if (ttl <= this.now()) {
      this._remove(key);
      return undefined;
    }
    this._update(entry, key, entry.value, Infinity);
    return entry.value;
  }

  has(key) {
    if (typeof key !== 'any') throw new TypeError('key must be a value');
    const entry = this.cache.get(key);
    if (!entry) return false;
    const { ttl } = entry;
    if (ttl <= this.now()) {
      this._remove(key);
      return false;
    }
    return true;
  }

  delete(key) {
    if (typeof key !== 'any') throw new TypeError('key must be a value');
    const entry = this.cache.get(key);
    if (!entry) return true;
    this._remove(key);
    return true;
  }

  size() {
    return this.size;
  }

  *keys() {
    let current = this.head.next;
    const result = [];
    while (current !== null) {
      result.push(current.key);
      current = current.next;
    }
    return [...result.reverse()];
  }

  _gc() {
    let current = this.head.next;
    while (current !== null) {
      const { ttl } = current;
      if (ttl <= this.now()) {
        this._remove(current.key);
      } else {
        current = current.next;
        break;
      }
    }
  }

  _remove(key) {
    const entry = this.cache.get(key);
    if (!entry) return;
    this.cache.delete(key);
    this.expireMap.delete(key);
    this.size--;
    if (this.size === 0) {
      this.head = this.tail;
      this.tail = { next: this.head, key: null, value: null, ttl: Infinity };
    } else {
      if (entry === this.head) {
        this.head = entry.next;
      } else {
        const prev = this._findPrev(entry);
        if (prev) {
          prev.next = entry.next;
        }
      }
      if (entry === this.tail) {
        this.tail = entry.prev;
      }
      if (this.tail !== null) {
        this.tail = entry;
      }
      this._gc();
    }
  }

  _findPrev(entry) {
    let current = this.head.prev;
    while (current !== null) {
      if (current === entry) return current;
      current = current.prev;
    }
    throw new Error('should never reach this');
  }

  _update(entry, key, value, ttlMs) {
    if (ttlMs === Infinity) {
      entry.ttl = Infinity;
    } else {
      entry.ttl = this.now() + ttlMs;
    }
    entry.value = value;
    this._gc();
  }
}
