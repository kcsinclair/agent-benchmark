export class LruTtlCache {
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this.capacity = capacity;
    this.defaultTtlMs = defaultTtlMs;
    this.now = now;
    this.map = new Map(); // key -> { value, expiryTime }
    this.accessOrder = new Map(); // key -> timestamp for LRU tracking
  }

  _purgeExpired() {
    const now = this.now();
    for (const [key, entry] of this.map.entries()) {
      if (entry.expiryTime !== Infinity && now >= entry.expiryTime) {
        this.map.delete(key);
        this.accessOrder.delete(key);
      }
    }
  }

  _ensureCapacity() {
    // Remove expired entries first
    this._purgeExpired();
    
    // If still over capacity, remove LRU entries
    while (this.map.size > this.capacity) {
      // Get the oldest key from accessOrder
      const oldestKey = this.accessOrder.keys().next().value;
      if (oldestKey !== undefined) {
        this.map.delete(oldestKey);
        this.accessOrder.delete(oldestKey);
      }
    }
  }

  set(key, value, ttlMs = this.defaultTtlMs) {
    const expiryTime = ttlMs === Infinity ? Infinity : this.now() + ttlMs;
    
    // Update access order
    this.accessOrder.delete(key); // Remove if exists
    this.accessOrder.set(key, this.now()); // Add to end
    
    this.map.set(key, { value, expiryTime });
    
    // Ensure capacity
    this._ensureCapacity();
    
    return this;
  }

  get(key) {
    const entry = this.map.get(key);
    if (entry === undefined) {
      return undefined;
    }
    
    // Check if expired
    if (entry.expiryTime !== Infinity && this.now() >= entry.expiryTime) {
      this.map.delete(key);
      this.accessOrder.delete(key);
      return undefined;
    }
    
    // Update access order
    this.accessOrder.delete(key);
    this.accessOrder.set(key, this.now());
    
    return entry.value;
  }

  has(key) {
    const entry = this.map.get(key);
    if (entry === undefined) {
      return false;
    }
    
    // Check if expired
    if (entry.expiryTime !== Infinity && this.now() >= entry.expiryTime) {
      this.map.delete(key);
      this.accessOrder.delete(key);
      return false;
    }
    
    return true;
  }

  delete(key) {
    const deleted = this.map.delete(key);
    this.accessOrder.delete(key);
    return deleted;
  }

  get size() {
    this._purgeExpired();
    return this.map.size;
  }

  keys() {
    this._purgeExpired();
    // Create array from accessOrder keys in reverse order (most recent first)
    return Array.from(this.accessOrder.keys()).reverse();
  }
}
