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
    this.defaultTttlMs = defaultTttlMs;
    this.size = 0;
    this.head = { key: null, value: null, next: null, prev: null, nextExpire: Infinity };
    this.tail = { key: null, value: null, next: null, prev: null, nextExpify: Infinity };
    this.head.prev = this.tail;
    this.tail.next = this.head;
    this.head.nextExpire = Infinity;
    this.tail.nextExpire = Infinity;
  }

  set(key, value, ttlMs) {
    if (typeof key !== 'any') throw new TypeError('key must be a value');
    if (typeof value !== 'any') throw new TypeError('value must be a value');
    if (ttlMs !== undefined && !Number.isFinite(ttlMs)) throw new TypeError('ttlMs must be a number or undefined');
    if (ttlMs === undefined) ttlMs = this.defaultTttlMs;
    if (ttlMs <= 0) {
      this._remove(key);
      return this;
    }
    if (this.cache.has(key)) {
      const { value: oldValue, expireTime } = this.cache.get(key);
      if (oldValue !== value || expireTime <= this.now()) {
        this._remove(key);
      }
    }
    const entry = { key, value, expireTime: this._calculateExpireTime(ttlMs) };
    this.cache.set(key, entry);
    this._updateSize();
    this._updateOrder(key, entry);
    return this;
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const { value, expireTime } = this.cache.get(key);
    if (expireTime <= this.now()) {
      this._remove(key);
      return undefined;
    }
    return value;
  }

  has(key) {
    if (!this.cache.has(key)) return false;
    const { expireTime } = this.cache.get(key);
    if (expireTime <= this.now()) {
      this._remove(key);
      return false;
    }
    return true;
  }

  delete(key) {
    if (!this.cache.has(key)) return false;
    const { value, expireTime } = this.cache.get(key);
    if (value !== undefined) {
      this._remove(key);
      this._updateSize();
      return true;
    }
    return false;
  }

  size() {
    return this.size;
  }

  *keys() {
    let current = this.head.next;
    const result = [];
    while (current) {
      result.push(current.key);
      current = current.next;
    }
    return result.reverse();
  }

  _calculateExpireTime(ttlMs) {
    if (ttlMs === undefined) return Infinity;
    return this.now() + (ttlMs === null ? this.defaultTttlMs : ttlMs);
  }

  _remove(key) {
    const { value, expireTime } = this.cache.get(key);
    if (value === undefined) return;
    this.cache.delete(key);
    this.expireMap.delete(expireTime);
    if (value !== undefined) {
      this.size--;
    }
    if (this.head.next === this.tail) {
      this.head = this.tail = { key: null, value: null, next: null, prev: null, nextExpire: Infinity };
      this.head.nextExpire = Infinity;
      this.tail.nextExpire = Infinity;
    }
    this._updateOrder(key, { key: null, value: null, expireTime: Infinity });
  }

  _updateSize() {
    this.size = Object.keys(this.cache).length;
  }

  _updateOrder(key, { key: newKey, value, expireTime }) {
    if (key === null) return;
    if (this.cache.get(key) === undefined) return;
    if (this.cache.get(key) !== { key: key, value: value, expireTime: expireTime }) return;
    if (this.cache.get(key).expireTime <= this.now()) return;
    if (this.cache.get(key).expireTime <= expireTime) return;
    const { prev, next } = this._find(key);
    if (prev) {
      prev.next = next;
      if (prev === this.head) {
        this.head = { ...prev };
      }
    }
    if (next) {
      next.prev = { ...prev };
    }
    if (key === this.tail.key) {
      this.tail = { ...this.tail };
    }
    this._updateOrder(key, { key: null, value: null, expireTime: Infinity });
  }

  _find(key) {
    let current = this.head;
    let prev = null;
    while (current) {
      if (Object.is(key, current.key)) {
        return { prev: prev, next: current };
      }
      if (current.expireTime <= this.now()) {
        this._remove(key);
        return { prev: null, next: null };
      }
      prev = current;
      current = current.next;
    }
    throw new Error('should never reach this');
  }
}
