# 🧠 Data Structures & Systems Design — LRU Cache & Event Scheduler

> A deep-dive implementation of two classic system-design problems, built from first principles with full complexity analysis, trade-off discussion, and production-readiness considerations.

---

## 📂 Project Structure

```
Data Structures & Systems Design/
├── lru_cache.py              # LRU Cache — HashMap + Doubly Linked List
├── event_scheduler.py        # Event Scheduler — Sort + Min-Heap
├── test_lru_cache.py          # 17 unit tests (normal, edge, stress)
├── test_event_scheduler.py    # 25 unit tests (normal, edge, stress)
└── README.md                  # ← You are here
```

---

## 🔖 Table of Contents

1. [Problem Statements](#1--problem-statements)
2. [Why These Data Structures? (From Brute Force to Optimal)](#2--why-these-data-structures-from-brute-force-to-optimal)
3. [Step-by-Step Implementation Walkthrough](#3--step-by-step-implementation-walkthrough)
4. [How to Run](#4--how-to-run)
5. [Test Results](#5--test-results)
6. [Final Discussion & Analysis](#6--final-discussion--analysis)
   - [6.1 Time & Space Complexity](#61-time--space-complexity-analysis)
   - [6.2 Trade-offs: Why HashMap + Doubly Linked List?](#62-trade-offs-why-hashmap--doubly-linked-list-for-lru)
   - [6.3 Future Proofing: Assigning Room Numbers](#63-future-proofing-assigning-specific-room-numbers)
   - [6.4 Concurrency: Thread-Safe LRU Cache](#64-concurrency-making-the-lru-cache-thread-safe)

---

## 1 · Problem Statements

### Problem 1 — LRU Cache

Build a **fixed-capacity key-value store** that always evicts the item that was accessed or written **least recently** when space runs out.

| Operation | Input | Output | Constraint |
|-----------|-------|--------|------------|
| `get(key)` | Any hashable key | Stored value, or `-1` if missing | **O(1)** time |
| `put(key, value)` | Key + value | None (evicts LRU item if at capacity) | **O(1)** time |

**Key edge cases:**
- `get` on a non-existent key → return `-1`
- `put` on an existing key → update value AND refresh recency (no eviction)
- `capacity = 1` → every new key evicts the only existing key
- `capacity = 0` → no-op store (degenerate case)

---

### Problem 2 — Event Scheduler

Given a list of `(start, end)` time intervals, answer two questions:

| Function | Question | Output |
|----------|----------|--------|
| `can_attend_all(events)` | Can one person attend all events without overlap? | `True` / `False` |
| `min_rooms_required(events)` | What's the minimum number of concurrent rooms? | Positive integer |

**Adjacency rule:** Events sharing only an endpoint (e.g., `(9,10)` and `(10,11)`) are **NOT** overlapping — the comparison is strictly `<`, never `≤`.

**Key edge cases:**
- Empty list → `True`, `0` rooms
- All events identical → `False`, rooms = number of events
- Nested intervals like `(9,12)` and `(10,11)` → overlap detected

---

## 2 · Why These Data Structures? (From Brute Force to Optimal)

### LRU Cache — Evolution of the Approach

#### ❌ Attempt 1: Plain List with Timestamps — O(n) per operation

The naive idea: store `(key, value, timestamp)` in a list. On every `get` or `put`, scan the entire list to find the key, update its timestamp, and on eviction, scan again for the minimum timestamp.

**Why it fails:** O(n) scans on every operation — completely unacceptable for a cache that is supposed to be fast by definition.

#### ❌ Attempt 2: HashMap with Timestamps — O(n) eviction

Improvement: use a HashMap for O(1) lookup. Store timestamps alongside values. On eviction, scan all entries to find the one with the smallest timestamp.

**Why it fails:** Get is O(1) ✅, but eviction still requires a full scan — O(n) ❌.

#### ❌ Attempt 3: Singly Linked List + HashMap — O(n) reordering

Use a singly linked list for ordering and a HashMap for lookup. The problem: to remove a node from the middle, you need its **predecessor**, which requires traversing from the head.

**Why it fails:** Can't splice a node out of a singly linked list without knowing the previous node — O(n) ❌.

#### ✅ Attempt 4: Doubly Linked List + HashMap — O(1) everything

The **core insight** is that we need two things simultaneously:
1. **Instant lookup by key** → HashMap gives O(1)
2. **Instant reordering** (move-to-front and remove-from-back) → Doubly Linked List gives O(1), once you have a pointer to the node

The HashMap stores `key → node pointer`. The DLL stores nodes in recency order. Every operation: look up the node in O(1), reposition it in O(1). **No scanning ever happens.**

```
HashMap:  { key1 → Node1, key2 → Node2, key3 → Node3 }
                    ↓            ↓            ↓
DLL:     [HEAD] ↔ [Node1] ↔ [Node2] ↔ [Node3] ↔ [TAIL]
          dummy    most                  least     dummy
                   recent                recent
```

---

### Event Scheduler — Evolution of the Approach

#### ❌ Attempt 1: Brute Force Pairwise — O(n²)

Compare every pair of events to check for overlaps. For `min_rooms`, simulate every moment in time. Neither scales.

#### ✅ Attempt 2: Sort + Linear Scan — O(n log n)

**Key insight:** Once events are sorted by start time, you never need to look backwards. An overlap can only exist with the immediately preceding event.

For `can_attend_all`: sort, then one linear pass checking `start < prev_end`.

#### ✅ Attempt 3: Sort + Min-Heap — O(n log n)

For `min_rooms_required`: the heap tracks **active rooms by their end times**. For each new event:
- If the earliest-ending room has freed up → reuse it (pop + push)
- If all rooms are busy → allocate a new room (push)

The heap size at the end = peak concurrency = minimum rooms needed.

---

## 3 · Step-by-Step Implementation Walkthrough

### 3.1 — LRU Cache: `lru_cache.py`

#### Step 1: Define the Node class

Each node in the doubly linked list holds a key-value pair plus `prev`/`next` pointers:

```python
class Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=0, value=0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None
```

**Why `__slots__`?** Prevents Python from creating a `__dict__` per node, saving ~40% memory per node — critical when the cache holds thousands of entries.

**Why store `key` in the node?** During eviction, we need to delete the evicted entry from the HashMap. Without the key stored in the node, we'd need a reverse lookup — O(n).

---

#### Step 2: Initialize the cache with sentinel nodes

```python
def __init__(self, capacity):
    self.capacity = capacity
    self.size = 0
    self.cache = {}          # key → Node (HashMap)
    self.head = Node()       # dummy head sentinel
    self.tail = Node()       # dummy tail sentinel
    self.head.next = self.tail
    self.tail.prev = self.head
```

**Why sentinel nodes?** They eliminate **all** null-pointer edge cases:
- Without sentinels: inserting into an empty list requires checking `if head is None`; removing the last node requires setting `head = None`. Every operation needs `if` checks.
- With sentinels: the list is never "empty" — it always has at least `head ↔ tail`. Insertions and removals are uniform — no special cases.

```
Empty cache:     [HEAD] ↔ [TAIL]
After one put:   [HEAD] ↔ [Node] ↔ [TAIL]
After eviction:  [HEAD] ↔ [TAIL]     (back to "empty", but pointers are never null)
```

---

#### Step 3: Internal DLL operations (all O(1))

```python
def _add_node(self, node):
    """Insert node right after head sentinel (most-recent position)."""
    node.prev = self.head
    node.next = self.head.next
    self.head.next.prev = node
    self.head.next = node

def _remove_node(self, node):
    """Detach node from its current position."""
    node.prev.next = node.next
    node.next.prev = node.prev

def _move_to_head(self, node):
    """Refresh recency: detach + re-insert at front."""
    self._remove_node(node)
    self._add_node(node)

def _pop_tail(self):
    """Remove and return the LRU node (just before tail sentinel)."""
    lru = self.tail.prev
    self._remove_node(lru)
    return lru
```

**Why separate `_remove_node` and `_add_node`?** The move-to-head operation (used by both `get` and `put`) is exactly `remove + add`. Keeping them separate follows the Single Responsibility Principle and reduces bug surface.

**Why `_pop_tail` returns the node?** The caller needs the node's key to delete it from the HashMap. Returning the node avoids a separate lookup.

---

#### Step 4: `get(key)` — O(1)

```python
def get(self, key):
    node = self.cache.get(key)    # O(1) HashMap lookup
    if node is None:
        return -1                 # Key doesn't exist
    self._move_to_head(node)      # O(1) refresh recency
    return node.value
```

**Flow:** HashMap lookup → move-to-head → return value. Three O(1) steps.

---

#### Step 5: `put(key, value)` — O(1)

```python
def put(self, key, value):
    if self.capacity == 0:
        return                    # Degenerate case: no-op store

    node = self.cache.get(key)    # O(1) check if key exists

    if node is not None:
        # UPDATE path: change value + refresh recency
        node.value = value
        self._move_to_head(node)
    else:
        # INSERT path
        if self.size == self.capacity:
            # EVICTION: remove LRU item
            evicted = self._pop_tail()
            del self.cache[evicted.key]
            self.size -= 1

        new_node = Node(key, value)
        self.cache[key] = new_node
        self._add_node(new_node)
        self.size += 1
```

**Why check `capacity == 0` first?** If capacity is zero, even a single put would attempt eviction on an empty structure — the sentinel's `prev` would be the head sentinel itself, causing corruption.

**Why update path does NOT evict:** Updating an existing key doesn't increase the number of entries. The size stays the same, so no eviction is needed — only a value change and recency refresh.

---

### 3.2 — Event Scheduler: `event_scheduler.py`

#### Step 1: `can_attend_all(events)` — O(n log n)

```python
def can_attend_all(events):
    if len(events) <= 1:
        return True

    sorted_events = sorted(events, key=lambda e: e[0])

    for i in range(1, len(sorted_events)):
        if sorted_events[i][0] < sorted_events[i - 1][1]:
            return False

    return True
```

**Why sort first?** After sorting by start time, overlaps can only occur between consecutive events. Without sorting, you'd need to compare every pair — O(n²).

**Why strict `<` (not `<=`)?** The adjacency rule says `(9,10)` and `(10,11)` are NOT overlapping. If we used `<=`, we'd incorrectly flag adjacent events as conflicts.

**Why check `len(events) <= 1` upfront?** Zero events = nothing to conflict with. One event = nothing to conflict against. This avoids unnecessary sorting.

---

#### Step 2: `min_rooms_required(events)` — O(n log n)

```python
import heapq

def min_rooms_required(events):
    if not events:
        return 0

    sorted_events = sorted(events, key=lambda e: e[0])

    heap = []                                    # Min-heap of end times
    heapq.heappush(heap, sorted_events[0][1])    # First event gets room 1

    for i in range(1, len(sorted_events)):
        start, end = sorted_events[i]

        if start >= heap[0]:                     # Earliest room freed up?
            heapq.heapreplace(heap, end)         # Reuse it (pop + push)
        else:
            heapq.heappush(heap, end)            # All busy → new room

    return len(heap)                             # Heap size = peak rooms
```

**Why a min-heap?** The heap always gives us the earliest-ending active room in O(log n). This directly models the real-world act of assigning the soonest-available room to the next event.

**Why `heapreplace` instead of `heappop` + `heappush`?** `heapreplace` is a single atomic operation that is more efficient than two separate calls — it avoids an unnecessary intermediate heap rebuild.

**Why does `len(heap)` give the answer?** The heap only grows when ALL active rooms are busy. It never shrinks below its peak size. So its final size equals the maximum concurrency at any point.

---

## 4 · How to Run

### Prerequisites

- Python 3.10+ (for `X | Y` type hints)
- `pytest` (install with `pip install pytest`)

### Run All Tests

```bash
cd "Data Structures & Systems Design"
python -m pytest test_lru_cache.py test_event_scheduler.py -v
```

### Quick Manual Test

```python
from lru_cache import LRUCache
from event_scheduler import can_attend_all, min_rooms_required

# LRU Cache
cache = LRUCache(2)
cache.put(1, 10)
cache.put(2, 20)
print(cache.get(1))    # 10
cache.put(3, 30)       # evicts key 2
print(cache.get(2))    # -1

# Event Scheduler
events = [(9, 10), (9, 11), (11, 12)]
print(can_attend_all(events))      # False
print(min_rooms_required(events))  # 2
```

---

## 5 · Test Results

**42 tests passed in 1.76 seconds.**

```
test_lru_cache.py::TestLRUCacheNormal::test_access_refreshes_recency       PASSED
test_lru_cache.py::TestLRUCacheNormal::test_basic_get_and_put              PASSED
test_lru_cache.py::TestLRUCacheNormal::test_eviction_of_lru_item           PASSED
test_lru_cache.py::TestLRUCacheNormal::test_multiple_evictions             PASSED
test_lru_cache.py::TestLRUCacheNormal::test_update_existing_key            PASSED
test_lru_cache.py::TestLRUCacheEdge::test_accessing_same_key_repeatedly    PASSED
test_lru_cache.py::TestLRUCacheEdge::test_capacity_one                     PASSED
test_lru_cache.py::TestLRUCacheEdge::test_capacity_zero                    PASSED
test_lru_cache.py::TestLRUCacheEdge::test_contains_without_recency_change  PASSED
test_lru_cache.py::TestLRUCacheEdge::test_get_on_empty_cache               PASSED
test_lru_cache.py::TestLRUCacheEdge::test_get_on_missing_key               PASSED
test_lru_cache.py::TestLRUCacheEdge::test_put_update_refreshes_recency     PASSED
test_lru_cache.py::TestLRUCacheEdge::test_sequential_puts_fill_to_capacity PASSED
test_lru_cache.py::TestLRUCacheEdge::test_size_never_exceeds_capacity      PASSED
test_lru_cache.py::TestLRUCacheEdge::test_update_does_not_evict            PASSED
test_lru_cache.py::TestLRUCacheStress::test_large_insert_cycle             PASSED
test_lru_cache.py::TestLRUCacheStress::test_repeated_get_put_same_key      PASSED
test_event_scheduler.py::TestCanAttendAllNormal::test_mixed_some_overlap   PASSED
test_event_scheduler.py::TestCanAttendAllNormal::test_non_overlapping      PASSED
test_event_scheduler.py::TestCanAttendAllNormal::test_three_simultaneous   PASSED
test_event_scheduler.py::TestCanAttendAllNormal::test_two_overlapping      PASSED
test_event_scheduler.py::TestMinRoomsNormal::test_mixed_some_overlap       PASSED
test_event_scheduler.py::TestMinRoomsNormal::test_non_overlapping          PASSED
test_event_scheduler.py::TestMinRoomsNormal::test_three_simultaneous       PASSED
test_event_scheduler.py::TestMinRoomsNormal::test_two_overlapping          PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_adjacent_boundary      PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_all_identical          PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_empty_list             PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_nested_events          PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_reverse_sorted         PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_single_event           PASSED
test_event_scheduler.py::TestCanAttendAllEdge::test_two_adjacent_chains    PASSED
test_event_scheduler.py::TestMinRoomsEdge::test_adjacent_boundary          PASSED
test_event_scheduler.py::TestMinRoomsEdge::test_all_identical              PASSED
test_event_scheduler.py::TestMinRoomsEdge::test_empty_list                 PASSED
test_event_scheduler.py::TestMinRoomsEdge::test_nested_events              PASSED
test_event_scheduler.py::TestMinRoomsEdge::test_reverse_sorted             PASSED
test_event_scheduler.py::TestMinRoomsEdge::test_single_event               PASSED
test_event_scheduler.py::TestSchedulerStress::test_boundary_rule_invariant PASSED
test_event_scheduler.py::TestSchedulerStress::test_large_fully_overlapping PASSED
test_event_scheduler.py::TestSchedulerStress::test_large_non_overlapping   PASSED
test_event_scheduler.py::TestSchedulerStress::test_unsorted_matches_sorted PASSED

========================= 42 passed in 1.76s =========================
```

| Category | LRU Cache | Event Scheduler | Total |
|----------|-----------|-----------------|-------|
| Normal   | 5         | 8               | 13    |
| Edge     | 10        | 13              | 23    |
| Stress   | 2         | 4               | 6     |
| **Total**| **17**    | **25**          | **42**|

---

## 6 · Final Discussion & Analysis

### 6.1 Time & Space Complexity Analysis

#### LRU Cache — All Operations O(1)

| Operation | Best | Average | Worst | Justification |
|-----------|------|---------|-------|---------------|
| `get(key)` — miss | O(1) | O(1) | O(1) | Single HashMap lookup, returns `-1` |
| `get(key)` — hit | O(1) | O(1) | O(1) | HashMap lookup + 4 pointer updates (detach) + 2 pointer updates (insert at head) |
| `put(key, val)` — update | O(1) | O(1) | O(1) | HashMap lookup + value assignment + move-to-head (6 pointer updates) |
| `put(key, val)` — insert (no eviction) | O(1) | O(1) | O(1) | HashMap insert + node creation + 2 pointer updates |
| `put(key, val)` — insert with eviction | O(1) | O(1) | O(1) | Same as above + eviction: 4 pointer updates + HashMap delete |
| **Space** | — | — | — | **O(capacity)** — at most `capacity` nodes + 2 sentinels + HashMap entries |

**Why truly O(1):** Every operation does a fixed number of steps regardless of cache size. The HashMap lookup is O(1) amortized. The linked list operations involve exactly 4–6 pointer reassignments — never a loop, never a scan.

#### Event Scheduler

| Function | Best | Average | Worst | Space | Justification |
|----------|------|---------|-------|-------|---------------|
| `can_attend_all` — empty/single | O(1) | — | — | O(1) | Early return, no sorting needed |
| `can_attend_all` — general | O(n log n) | O(n log n) | O(n log n) | O(n)* | Python's Timsort is O(n log n); linear scan is O(n) |
| `min_rooms_required` — empty | O(1) | — | — | O(1) | Early return |
| `min_rooms_required` — general | O(n log n) | O(n log n) | O(n log n) | O(n) | Sort O(n log n) + n heap operations each O(log n) = O(n log n); heap stores at most n end times |

*\*O(n) for the sorted copy; the scan itself uses O(1) extra space.*

**Why O(n log n) is optimal for the scheduler:** Any comparison-based algorithm that determines ordering among n elements requires Ω(n log n) comparisons. Since we must consider the relative order of all events, we can't beat O(n log n).

---

### 6.2 Trade-offs: Why HashMap + Doubly Linked List for LRU?

The LRU cache has **two competing requirements** that individually point to different data structures:

| Requirement | What It Needs | Best Data Structure |
|-------------|---------------|---------------------|
| Fast lookup by key | O(1) key → value | **HashMap** |
| Fast recency tracking & eviction | O(1) move-to-front, O(1) remove-from-back | **Doubly Linked List** |

**No single data structure satisfies both.** Here's why each alternative fails:

| Alternative | Lookup | Reorder | Eviction | Verdict |
|-------------|--------|---------|----------|---------|
| Plain Array / List | O(n) scan | O(n) shift | O(n) scan | ❌ Too slow on everything |
| HashMap + Timestamps | O(1) | O(1) update | O(n) scan for min | ❌ Eviction breaks the O(1) requirement |
| Singly Linked List + HashMap | O(1) | O(n) — can't splice without `prev` pointer | O(1) at tail | ❌ Reorder is O(n) |
| **Doubly Linked List + HashMap** | **O(1)** | **O(1)** — splice with `prev` + `next` | **O(1)** at tail | ✅ **Optimal** |
| Python `OrderedDict` | O(1) | O(1) | O(1) | ✅ Works but hides the design |

**The synergy:**
- The **HashMap** gives us the pointer to the node in O(1)
- The **Doubly Linked List** uses that pointer to do O(1) repositioning (because each node knows both its predecessor and successor)
- **Sentinel nodes** eliminate all edge-case `if` checks for empty/single-node lists

**Why not just use `OrderedDict`?** Python's `collections.OrderedDict` is essentially a pre-packaged HashMap + DLL. It works, but:
1. It hides the architectural understanding — unsuitable for interviews or design exercises
2. It doesn't demonstrate knowledge of pointer manipulation
3. The custom implementation gives full control over eviction policy extensions (e.g., LFU, TTL-based expiry)

**Trade-off summary:**

| Aspect | HashMap + DLL | OrderedDict |
|--------|---------------|-------------|
| Performance | O(1) all ops | O(1) all ops |
| Transparency | Full visibility into internals | Black-box |
| Extensibility | Easy to add LFU, TTL, sharding | Limited |
| Implementation effort | Medium-high | Trivial |
| Interview suitability | ✅ Demonstrates design skill | ❌ Appears as library trivia |

---

### 6.3 Future Proofing: Assigning Specific Room Numbers

**Question:** How would you modify the scheduler to assign specific room numbers (e.g., "Room A", "Room B") to each event?

**Answer — Three changes to `min_rooms_required`:**

#### Change 1: Heap stores `(end_time, room_name)` tuples instead of just end times

```python
# BEFORE:  heap contains [end_time, end_time, ...]
# AFTER:   heap contains [(end_time, "Room A"), (end_time, "Room B"), ...]
```

The min-heap still orders by `end_time` (first element of tuple), so the room-reuse logic is unchanged.

#### Change 2: Maintain an available-rooms pool

```python
from collections import deque

available_rooms = deque()    # pool of free room names
room_counter = 0             # for generating new names

def get_room():
    nonlocal room_counter
    if available_rooms:
        return available_rooms.popleft()    # reuse a freed room
    room_counter += 1
    return f"Room {chr(64 + room_counter)}"  # "Room A", "Room B", ...

def release_room(name):
    available_rooms.append(name)
```

#### Change 3: Record assignments in an output dictionary

```python
def min_rooms_with_assignments(events):
    if not events:
        return 0, {}

    sorted_events = sorted(events, key=lambda e: (e[0], e[1]))
    assignments = {}       # event → room name
    heap = []

    for event in sorted_events:
        start, end = event

        if heap and start >= heap[0][0]:
            _, freed_room = heapq.heappop(heap)    # room freed up
        else:
            freed_room = get_room()                 # allocate new

        assignments[event] = freed_room
        heapq.heappush(heap, (end, freed_room))

    return len(set(assignments.values())), assignments
```

**Example output:**
```
Input:  [(9,10), (9,11), (11,12)]
Output: {
    (9,10):  "Room A",
    (9,11):  "Room B",
    (11,12): "Room A"    ← Room A freed up at t=10, reused
}
Rooms needed: 2
```

**Design decision — Fixed vs. fungible rooms:**
- If rooms have **fixed identities** (physical rooms with locations), keep the room name tied to the heap entry and always reuse the same room object.
- If rooms are **fungible** (any available room works), names from the pool can be assigned in any order.

**Complexity impact:** None — the algorithm stays O(n log n). The only addition is O(1) dictionary writes and pool operations per event.

---

### 6.4 Concurrency: Making the LRU Cache Thread-Safe

**Question:** What changes would be required to make the LRU Cache thread-safe?

**The problem:** In a concurrent environment, two threads could simultaneously call `get` or `put`. Without synchronization, one thread could be mid-pointer-surgery (detaching a node) while another thread reads the corrupt intermediate state. This leads to data races, lost updates, and crashes.

#### Layer 1: Coarse-Grained Locking (Simplest — Recommended for This Project)

Wrap every `get` and `put` in a single **mutex lock**:

```python
import threading

class ThreadSafeLRUCache(LRUCache):
    def __init__(self, capacity):
        super().__init__(capacity)
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:               # only one thread at a time
            return super().get(key)

    def put(self, key, value):
        with self._lock:
            super().put(key, value)
```

| Pros | Cons |
|------|------|
| Correct and simple to reason about | Becomes a bottleneck under high concurrency |
| Easy to test and debug | All threads queue up — no parallelism |
| No risk of subtle data races | Read-heavy workloads are serialized unnecessarily |

#### Layer 2: Read-Write Lock (Limited Benefit for LRU)

Use a **Read-Write Lock** (`threading.RWLock`): multiple readers can proceed simultaneously, but writers get exclusive access.

**The catch for LRU:** Even `get()` mutates the ordering (move-to-head), so it requires a **write lock** — not a read lock. This means RWLock provides almost no benefit for an LRU cache specifically.

#### Layer 3: Segmented/Sharded Cache (Production-Scale)

Divide the cache into **N independent shards**, each with its own HashMap, DLL, and lock:

```python
class ShardedLRUCache:
    def __init__(self, capacity, num_shards=16):
        shard_cap = max(1, capacity // num_shards)
        self.shards = [ThreadSafeLRUCache(shard_cap) for _ in range(num_shards)]
        self.num_shards = num_shards

    def _get_shard(self, key):
        return self.shards[hash(key) % self.num_shards]

    def get(self, key):
        return self._get_shard(key).get(key)

    def put(self, key, value):
        self._get_shard(key).put(key, value)
```

| Pros | Cons |
|------|------|
| Threads on different keys rarely contend | LRU ordering is per-shard, not global |
| Used in production: Memcached, Guava Cache | Slightly more complex capacity management |
| Near-linear scalability with shard count | Eviction is approximate (least-recently-used within each shard) |

#### Layer 4: Lock-Free Structures (Ultra-High Performance)

Use **atomic compare-and-swap (CAS)** operations instead of locks. Nodes are updated using `CAS(expected, new)` — if another thread modified the node between the read and write, the CAS fails and the operation retries.

**This is extremely complex** for a doubly linked list due to the ABA problem and the need to atomically update multiple pointers. Reserved for scenarios where lock overhead is measurable in profiling.

#### Recommendation

| Scenario | Approach |
|----------|----------|
| Single-threaded application | No locking needed |
| Moderate concurrency (most apps) | **Layer 1: Mutex** — simple, correct, fast enough |
| High concurrency, many distinct keys | **Layer 3: Sharded** — near-linear scaling |
| Ultra-low latency (few μs matter) | Layer 4: Lock-free — only if profiling proves it's necessary |

For this assignment: **Layer 1 (simple mutex)** is the recommended implementation. Mention Layer 3 as the production-scale extension.

---

## 📚 References

- LRU Cache: [LeetCode #146](https://leetcode.com/problems/lru-cache/)
- Meeting Rooms: [LeetCode #252](https://leetcode.com/problems/meeting-rooms/) & [#253](https://leetcode.com/problems/meeting-rooms-ii/)
- Python `heapq` module: [docs.python.org](https://docs.python.org/3/library/heapq.html)
- Thread safety patterns: [Python `threading` docs](https://docs.python.org/3/library/threading.html)
