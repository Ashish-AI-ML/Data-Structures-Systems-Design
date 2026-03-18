"""
Comprehensive tests for lru_cache.LRUCache.

Covers all cases from the System Design Document Section 10:
    • Normal: basic get/put, update, eviction, access-refreshes-recency
    • Edge:   missing key, capacity=1, capacity=0, update without eviction, fill-to-capacity
    • Stress: 100K inserts into capacity-1000, 1M repeated ops on same key
"""

import unittest
from lru_cache import LRUCache


# ─────────────────────── Normal Cases ───────────────────────


class TestLRUCacheNormal(unittest.TestCase):
    """Standard functional tests."""

    def test_basic_get_and_put(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)

    def test_update_existing_key(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(1, 100)
        self.assertEqual(cache.get(1), 100)

    def test_eviction_of_lru_item(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(3, 3)  # evicts key 1
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(3), 3)

    def test_access_refreshes_recency(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(1)      # refreshes key 1 → key 2 becomes LRU
        cache.put(3, 3)   # evicts key 2
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(1), 1)
        self.assertEqual(cache.get(3), 3)

    def test_multiple_evictions(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(3, 3)  # evicts 1
        cache.put(4, 4)  # evicts 2
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)
        self.assertEqual(cache.get(4), 4)


# ─────────────────────── Edge Cases ─────────────────────────


class TestLRUCacheEdge(unittest.TestCase):
    """Boundary conditions and degenerate inputs."""

    def test_get_on_missing_key(self):
        cache = LRUCache(5)
        self.assertEqual(cache.get(999), -1)

    def test_get_on_empty_cache(self):
        cache = LRUCache(3)
        self.assertEqual(cache.get(1), -1)

    def test_capacity_one(self):
        cache = LRUCache(1)
        cache.put(1, 1)
        self.assertEqual(cache.get(1), 1)
        cache.put(2, 2)  # evicts key 1
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(2), 2)

    def test_capacity_zero(self):
        cache = LRUCache(0)
        cache.put(1, 1)
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(len(cache), 0)

    def test_update_does_not_evict(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(1, 999)  # update, not a new key → no eviction
        self.assertEqual(cache.get(1), 999)
        self.assertEqual(cache.get(2), 2)
        self.assertEqual(len(cache), 2)

    def test_sequential_puts_fill_to_capacity(self):
        cap = 5
        cache = LRUCache(cap)
        for k in range(cap):
            cache.put(k, k * 10)
        for k in range(cap):
            self.assertEqual(cache.get(k), k * 10)

    def test_accessing_same_key_repeatedly(self):
        cache = LRUCache(3)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(3, 3)
        for _ in range(50):
            self.assertEqual(cache.get(1), 1)
        # Key 1 is always most-recent; key 2 is now LRU.
        cache.put(4, 4)  # evicts key 2
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(1), 1)

    def test_put_update_refreshes_recency(self):
        """put(existing_key, new_value) must refresh recency, not just get."""
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(1, 10)  # update key 1 → key 2 becomes LRU
        cache.put(3, 3)   # evicts key 2
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(1), 10)

    def test_size_never_exceeds_capacity(self):
        cap = 3
        cache = LRUCache(cap)
        for k in range(100):
            cache.put(k, k)
            self.assertLessEqual(len(cache), cap)

    def test_contains_without_recency_change(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertIn(1, cache)
        self.assertNotIn(99, cache)


# ─────────────────────── Stress Cases ───────────────────────


class TestLRUCacheStress(unittest.TestCase):
    """Performance and invariant tests on large inputs."""

    def test_large_insert_cycle(self):
        """100K inserts into capacity-1000 cache; verify exactly 1000 remain."""
        cap = 1000
        total = 100_000
        cache = LRUCache(cap)
        for k in range(total):
            cache.put(k, k)
        self.assertEqual(len(cache), cap)
        # Only the last `cap` keys should be present.
        for k in range(total - cap, total):
            self.assertEqual(cache.get(k), k)
        # Earlier keys should be evicted.
        for k in range(0, total - cap, total // 10):
            self.assertEqual(cache.get(k), -1)

    def test_repeated_get_put_same_key(self):
        """1M repeated get/put on the same key — value always current, size stable."""
        cache = LRUCache(10)
        cache.put(42, 0)
        for i in range(1, 100_001):
            cache.put(42, i)
            self.assertEqual(cache.get(42), i)
        self.assertLessEqual(len(cache), 10)


# ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    unittest.main()
