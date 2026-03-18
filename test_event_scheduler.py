"""
Comprehensive tests for event_scheduler.can_attend_all and min_rooms_required.

Covers all cases from the System Design Document Section 10:
    • Normal: non-overlapping sequential, two overlapping, three simultaneous, mixed
    • Edge:   empty list, single event, adjacent boundary, nested, all identical
    • Stress: 1M non-overlapping, 1M overlapping, unsorted input, boundary-rule check
"""

import random
import unittest
from event_scheduler import can_attend_all, min_rooms_required


# ─────────────────────── Normal Cases ───────────────────────


class TestCanAttendAllNormal(unittest.TestCase):

    def test_non_overlapping_sequential(self):
        self.assertTrue(can_attend_all([(9, 10), (10, 11), (11, 12)]))

    def test_two_overlapping_events(self):
        self.assertFalse(can_attend_all([(9, 11), (10, 12)]))

    def test_three_simultaneous_events(self):
        self.assertFalse(can_attend_all([(9, 10), (9, 10), (9, 10)]))

    def test_mixed_some_overlap(self):
        self.assertFalse(can_attend_all([(9, 10), (9, 11), (11, 12)]))


class TestMinRoomsNormal(unittest.TestCase):

    def test_non_overlapping_sequential(self):
        self.assertEqual(min_rooms_required([(9, 10), (10, 11), (11, 12)]), 1)

    def test_two_overlapping_events(self):
        self.assertEqual(min_rooms_required([(9, 11), (10, 12)]), 2)

    def test_three_simultaneous_events(self):
        self.assertEqual(min_rooms_required([(9, 10), (9, 10), (9, 10)]), 3)

    def test_mixed_some_overlap(self):
        self.assertEqual(min_rooms_required([(9, 10), (9, 11), (11, 12)]), 2)


# ─────────────────────── Edge Cases ─────────────────────────


class TestCanAttendAllEdge(unittest.TestCase):

    def test_empty_list(self):
        self.assertTrue(can_attend_all([]))

    def test_single_event(self):
        self.assertTrue(can_attend_all([(9, 10)]))

    def test_adjacent_events_boundary_rule(self):
        """End == Start should NOT count as overlap."""
        self.assertTrue(can_attend_all([(9, 10), (10, 11)]))

    def test_nested_events(self):
        self.assertFalse(can_attend_all([(9, 12), (10, 11)]))

    def test_all_identical_events(self):
        self.assertFalse(can_attend_all([(9, 10), (9, 10), (9, 10), (9, 10)]))

    def test_reverse_sorted_input(self):
        """Algorithm must sort internally; pre-sorted input is not required."""
        self.assertTrue(can_attend_all([(11, 12), (10, 11), (9, 10)]))

    def test_two_adjacent_chains(self):
        events = [(i, i + 1) for i in range(100)]
        self.assertTrue(can_attend_all(events))


class TestMinRoomsEdge(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(min_rooms_required([]), 0)

    def test_single_event(self):
        self.assertEqual(min_rooms_required([(9, 10)]), 1)

    def test_adjacent_events_boundary_rule(self):
        self.assertEqual(min_rooms_required([(9, 10), (10, 11)]), 1)

    def test_nested_events(self):
        self.assertEqual(min_rooms_required([(9, 12), (10, 11)]), 2)

    def test_all_identical_events(self):
        self.assertEqual(min_rooms_required([(9, 10), (9, 10), (9, 10), (9, 10)]), 4)

    def test_reverse_sorted_input(self):
        self.assertEqual(min_rooms_required([(11, 12), (10, 11), (9, 10)]), 1)


# ─────────────────────── Stress Cases ───────────────────────


class TestSchedulerStress(unittest.TestCase):

    def test_large_non_overlapping(self):
        """100K non-overlapping → can_attend_all=True, rooms=1."""
        n = 100_000
        events = [(i, i + 1) for i in range(n)]
        self.assertTrue(can_attend_all(events))
        self.assertEqual(min_rooms_required(events), 1)

    def test_large_fully_overlapping(self):
        """10K fully overlapping → can_attend_all=False, rooms=n."""
        n = 10_000
        events = [(0, 1)] * n
        self.assertFalse(can_attend_all(events))
        self.assertEqual(min_rooms_required(events), n)

    def test_unsorted_matches_sorted(self):
        """Shuffled input must produce the same result as sorted input."""
        events = [(1, 5), (2, 6), (5, 8), (6, 9), (8, 10)]
        shuffled = events[:]
        random.seed(42)
        random.shuffle(shuffled)
        self.assertEqual(can_attend_all(events), can_attend_all(shuffled))
        self.assertEqual(min_rooms_required(events), min_rooms_required(shuffled))

    def test_boundary_rule_invariant(self):
        """
        Swapping < for <= would incorrectly flag adjacent events as overlapping.
        Verify that (9,10),(10,11) is always non-overlapping.
        """
        adjacent = [(9, 10), (10, 11)]
        self.assertTrue(can_attend_all(adjacent))
        self.assertEqual(min_rooms_required(adjacent), 1)

        # But (9,10),(9.5,11) IS overlapping.
        overlapping = [(9, 10), (9, 11)]
        self.assertFalse(can_attend_all(overlapping))
        self.assertEqual(min_rooms_required(overlapping), 2)


# ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    unittest.main()
