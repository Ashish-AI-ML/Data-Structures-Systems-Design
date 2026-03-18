"""
Event Scheduler — Overlap Detection & Minimum Room Allocation
==============================================================

Two functions for interval scheduling:
    1. can_attend_all   — Can one person attend every event without overlap?
    2. min_rooms_required — What is the minimum number of concurrent rooms needed?

Adjacency Rule:
    Events sharing only an endpoint (e.g., (9,10) and (10,11)) are NOT overlapping.
    The overlap condition is strictly:  start_b < end_a  (not ≤).

Complexity:
    can_attend_all:    O(n log n) time  |  O(1) extra space (in-place sort)
    min_rooms_required: O(n log n) time  |  O(n) space (heap of end times)
"""

from __future__ import annotations

import heapq
from typing import Sequence


def can_attend_all(events: Sequence[tuple[int, int]]) -> bool:
    """
    Determine whether a single person can attend all events without overlap.

    Parameters
    ----------
    events : sequence of (start, end) tuples
        Each tuple represents an event's time interval.

    Returns
    -------
    bool
        True if no two events overlap; False otherwise.

    Examples
    --------
    >>> can_attend_all([(9, 10), (10, 11), (11, 12)])
    True
    >>> can_attend_all([(9, 11), (10, 12)])
    False
    >>> can_attend_all([])
    True
    """
    if len(events) <= 1:
        return True

    # Sort by start time; ties broken by end time (default tuple ordering).
    sorted_events = sorted(events, key=lambda e: e[0])

    for i in range(1, len(sorted_events)):
        # Overlap exists if the current event starts BEFORE the previous one ends.
        # Strictly < (not <=) because adjacent events are allowed.
        if sorted_events[i][0] < sorted_events[i - 1][1]:
            return False

    return True


def min_rooms_required(events: Sequence[tuple[int, int]]) -> int:
    """
    Calculate the minimum number of rooms (resources) needed so that all
    events can proceed without conflicts.

    Uses a min-heap of end times: for each new event, if the earliest-ending
    active room has already freed up, reuse it; otherwise allocate a new room.

    Parameters
    ----------
    events : sequence of (start, end) tuples
        Each tuple represents an event's time interval.

    Returns
    -------
    int
        The minimum number of concurrent rooms required.

    Examples
    --------
    >>> min_rooms_required([(9, 10), (10, 11), (11, 12)])
    1
    >>> min_rooms_required([(9, 11), (10, 12)])
    2
    >>> min_rooms_required([])
    0
    """
    if not events:
        return 0

    # Sort by start time.
    sorted_events = sorted(events, key=lambda e: e[0])

    # Min-heap of end times for currently active rooms.
    # Each entry represents a room that is busy until that end time.
    heap: list[int] = []
    heapq.heappush(heap, sorted_events[0][1])

    for i in range(1, len(sorted_events)):
        start, end = sorted_events[i]

        # If the earliest-ending room has freed up, reuse it.
        if start >= heap[0]:
            heapq.heapreplace(heap, end)  # pop smallest + push new end
        else:
            # All rooms are still busy — allocate a new one.
            heapq.heappush(heap, end)

    # The heap size equals the peak concurrency = minimum rooms needed.
    return len(heap)
