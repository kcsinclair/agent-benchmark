cache.set('k', 'v', 0);
expect(cache.get('k')).toBeUndefined();
expect(cache.has('k')).toBe(false);
