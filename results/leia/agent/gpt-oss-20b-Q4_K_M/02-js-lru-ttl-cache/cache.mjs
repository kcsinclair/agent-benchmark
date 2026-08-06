export class LruTtlCache {
  /**
   * @param {{ capacity: number, defaultTtlMs?: number, now?: () => number }} options
   */
  constructor({ capacity, defaultTtlMs = Infinity, now = () => Date.now() }) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer ≥ 1');
    }
    this._capacity = capacity;
    this._defaultTtlMs = defaultTtlMs;
    this._now = now;

    // Map of key -> node
    this._map = new Map();
    // Doubly linked list for LRU order
    this._head = null; // least recent
    this._tail = null; // most recent
    this._size = 0;

    // Min-heap of {expiry, node}
    this._heap = [];
  }

  // ---------- internal helpers ----------

  _heapPush(entry) {
    const heap = this._heap;
    heap.push(entry);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (heap[p].expiry <= entry.expiry) break;
      heap[i] = heap[p];
      i = p;
    }
    heap[i] = entry;
  }

  _heapPop() {
    const heap = this._heap;
    if (heap.length === 0) return undefined;
    const root = heap[0];
    const last = heap.pop();
    if (heap.length === 0) return root;
    let i = 0;
    const n = heap.length;
    while (true) {
      let l = i * 2 + 1;
      if (l >= n) break;
      let r = l + 1;
      let c = r < n && heap[r].expiry < heap[l].expiry ? r : l;
      if (heap[c].expiry >= last.expiry) break;
      heap[i] = heap[c];
      i = c;
    }
    heap[i] = last;
    return root;
  }

  _heapPeek() {
    return this._heap[0];
  }

  _purgeExpired() {
    const now = this._now();
    let entry = this._heapPeek();
    while (entry && entry.expiry <= now) {
      this._heapPop();
      const node = entry.node;
      const key = node.key;
      const mapNode = this._map.get(key);
      if (mapNode && mapNode.expiry === entry.expiry) {
        this._deleteNode(node);
      }
      entry = this._heapPeek();
    }
  }

  _deleteNode(node) {
    // remove from map
    this._map.delete(node.key);
    // remove from linked list
    if (node.prev) node.prev.next = node.next; else this._head = node.next;
    if (node.next) node.next.prev = node.prev; else this._tail = node.prev;
    node.prev = node.next = null;
    this._size--;
  }

  _moveToTail(node) {
    if (this._tail === node) return;
    // detach
    if (node.prev) node.prev.next = node.next; else this._head = node.next;
    if (node.next) node.next.prev = node.prev; else this._tail = node.prev;
    // attach at tail
    node.prev = this._tail;
    node.next = null;
    if (this._tail) this._tail.next = node;
    this._tail = node;
    if (!this._head) this._head = node;
  }

  // ---------- public API ----------

  set(key, value, ttlMs) {
    const now = this._now();
    const expiry = now + (ttlMs !== undefined ? ttlMs : this._defaultTtlMs);
    let node = this._map.get(key);
    if (node) {
      // update existing
      node.value = value;
      node.expiry = expiry;
      this._moveToTail(node);
    } else {
      // new node
      node = { key, value, expiry, prev: null, next: null };
      this._map.set(key, node);
      // add to tail
      if (this._tail) {
        this._tail.next = node;
        node.prev = this._tail;
      } else {
        this._head = node;
      }
      this._tail = node;
      this._size++;
    }
    // push to heap
    this._heapPush({ expiry, node });

    // Evict if over capacity
    this._purgeExpired();
    while (this._size > this._capacity) {
      // evict LRU
      const lru = this._head;
      if (!lru) break; // should not happen
      this._deleteNode(lru);
    }
    return this;
  }

  get(key) {
    const node = this._map.get(key);
    if (!node) return undefined;
    const now = this._now();
    if (node.expiry <= now) {
      this._deleteNode(node);
      return undefined;
    }
    this._moveToTail(node);
    return node.value;
  }

  has(key) {
    const node = this._map.get(key);
    if (!node) return false;
    const now = this._now();
    if (node.expiry <= now) {
      this._deleteNode(node);
      return false;
    }
    return true;
  }

  delete(key) {
    const node = this._map.get(key);
    if (!node) return false;
    this._deleteNode(node);
    return true;
  }

  get size() {
    this._purgeExpired();
    return this._size;
  }

  keys() {
    this._purgeExpired();
    const res = [];
    let node = this._tail;
    while (node) {
      res.push(node.key);
      node = node.prev;
    }
    return res;
  }
}
