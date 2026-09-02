// cache.mjs

export class LruTtlCache {
  #capacity;
  #defaultTtlMs;
  #now;
  #cache; // Map: key -> { value, expiry, prev, next }
  #head; // Most recently used
  #tail; // Least recently used

  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer >= 1');
    }

    this.#capacity = capacity;
    this.#defaultTtlMs = defaultTtlMs;
    this.#now = now;
    this.#cache = new Map();
    this.#head = null;
    this.#tail = null;
  }

  #isExpired(entry) {
    if (entry.expiry === Infinity) {
      return false;
    }
    return this.#now() >= entry.expiry;
  }

  #removeNode(key) {
    const entry = this.#cache.get(key);
    if (!entry) {
      return false;
    }

    if (entry.prev) {
      entry.prev.next = entry.next;
    } else {
      this.#head = entry.next;
    }

    if (entry.next) {
      entry.next.prev = entry.prev;
    } else {
      this.#tail = entry.prev;
    }

    this.#cache.delete(key);
    return true;
  }

  #moveToHead(key) {
    const entry = this.#cache.get(key);
    if (!entry || entry === this.#head) {
      return;
    }

    // Remove from current position
    if (entry.prev) {
      entry.prev.next = entry.next;
    }
    if (entry.next) {
      entry.next.prev = entry.prev;
    } else {
      // If it was the tail, update tail
      this.#tail = entry.prev;
    }

    // Move to head
    entry.next = this.#head;
    entry.prev = null;
    if (this.#head) {
      this.#head.prev = entry;
    }
    this.#head = entry;

    // If cache was empty, this is also the tail
    if (!this.#tail) {
      this.#tail = entry;
    }
  }

  #evictExpired() {
    let current = this.#tail;
    while (current) {
      if (this.#isExpired(current)) {
        const keyToRemove = current.key; // Store key before current becomes invalid
        current = current.prev; // Move to previous before removing
        this.#removeNode(keyToRemove);
      } else {
        current = current.prev;
      }
    }
  }

  set(key, value, ttlMs) {
    const currentTtlMs = ttlMs ?? this.#defaultTtlMs;
    const expiry = currentTtlMs === Infinity ? Infinity : this.#now() + currentTtlMs;

    if (this.#cache.has(key)) {
      const entry = this.#cache.get(key);
      entry.value = value;
      entry.expiry = expiry;
      this.#moveToHead(key);
    } else {
      // Check capacity before adding new entry
      if (this.#cache.size >= this.#capacity) {
        this.#evictExpired(); // Evict expired entries first
      }

      if (this.#cache.size >= this.#capacity) {
        // Still over capacity, evict LRU
        if (this.#tail) {
          this.#removeNode(this.#tail.key);
        }
      }

      const newEntry = { key, value, expiry, prev: null, next: null };
      this.#cache.set(key, newEntry);

      // Add to head of linked list
      newEntry.next = this.#head;
      if (this.#head) {
        this.#head.prev = newEntry;
      }
      this.#head = newEntry;

      if (!this.#tail) {
        this.#tail = newEntry;
      }
    }
    return this;
  }

  get(key) {
    const entry = this.#cache.get(key);
    if (!entry) {
      return undefined;
    }

    if (this.#isExpired(entry)) {
      this.#removeNode(key);
      return undefined;
    }

    this.#moveToHead(key);
    return entry.value;
  }

  has(key) {
    const entry = this.#cache.get(key);
    if (!entry) {
      return false;
    }

    if (this.#isExpired(entry)) {
      this.#removeNode(key);
      return false;
    }
    return true;
  }

  delete(key) {
    return this.#removeNode(key);
  }

  get size() {
    // Purge expired entries to get accurate size
    this.#evictExpired();
    return this.#cache.size;
  }

  keys() {
    this.#evictExpired(); // Ensure only live keys are returned

    const result = [];
    let current = this.#head;
    while (current) {
      result.push(current.key);
      current = current.next;
    }
    return result;
  }
}
