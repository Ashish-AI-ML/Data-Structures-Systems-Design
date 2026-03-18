"""
LRU Cache — HashMap + Doubly Linked List Implementation
========================================================

A fixed-capacity key-value store that evicts the least recently used item
when capacity is exceeded. Both get() and put() run in O(1) time.

Architecture:
    - A HashMap (dict) maps keys to their corresponding DLL nodes for O(1) lookup.
    - A Doubly Linked List maintains access-recency order:
        • Head sentinel's next → most recently used
        • Tail sentinel's prev → least recently used (eviction candidate)
    - Two sentinel nodes eliminate all null-pointer edge cases.

Complexity:
    Time:  O(1) for get and put (all cases)
    Space: O(capacity)
"""


class Node:
    """Doubly linked list node holding a key-value pair."""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev: "Node | None" = None
        self.next: "Node | None" = None

    def __repr__(self) -> str:
        return f"Node(key={self.key}, value={self.value})"


class LRUCache:
    """
    Least Recently Used Cache with O(1) get and put.

    Parameters
    ----------
    capacity : int
        Maximum number of key-value pairs the cache can hold.
        A capacity of 0 creates a no-op store (all puts are ignored).

    Examples
    --------
    >>> cache = LRUCache(2)
    >>> cache.put(1, 1)
    >>> cache.put(2, 2)
    >>> cache.get(1)
    1
    >>> cache.put(3, 3)        # evicts key 2 (LRU)
    >>> cache.get(2)
    -1
    >>> cache.put(4, 4)        # evicts key 1 (LRU after key 3 was inserted)
    >>> cache.get(1)
    -1
    >>> cache.get(3)
    3
    >>> cache.get(4)
    4
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.size = 0
        self.cache: dict[int, Node] = {}  # key → Node

        # Sentinel nodes — never hold real data.
        # head ↔ ... real nodes ... ↔ tail
        self.head = Node()  # dummy head (most-recent side)
        self.tail = Node()  # dummy tail (least-recent side)
        self.head.next = self.tail
        self.tail.prev = self.head

    # ------------------------------------------------------------------
    # Internal linked-list operations (all O(1))
    # ------------------------------------------------------------------

    def _add_node(self, node: Node) -> None:
        """Insert *node* right after the head sentinel (most-recent position)."""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: Node) -> None:
        """Detach *node* from its current position in the list."""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _move_to_head(self, node: Node) -> None:
        """Remove *node* from wherever it is and re-insert at the head (refresh recency)."""
        self._remove_node(node)
        self._add_node(node)

    def _pop_tail(self) -> Node:
        """Remove and return the node just before the tail sentinel (the LRU item)."""
        lru_node = self.tail.prev
        self._remove_node(lru_node)
        return lru_node

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: int) -> int:
        """
        Return the value for *key*, or -1 if not present.

        A successful get refreshes the key's recency (moves it to the front).
        """
        node = self.cache.get(key)
        if node is None:
            return -1
        # Key exists — refresh recency and return value.
        self._move_to_head(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        """
        Insert or update *key* with *value*.

        • If the key already exists, update its value and refresh recency.
        • If the key is new and the cache is at capacity, evict the LRU item first.
        • If capacity is 0, this is a no-op.
        """
        if self.capacity == 0:
            return

        node = self.cache.get(key)

        if node is not None:
            # ---- Update path ----
            node.value = value
            self._move_to_head(node)
        else:
            # ---- Insert path ----
            if self.size == self.capacity:
                # Evict the least recently used item.
                evicted = self._pop_tail()
                del self.cache[evicted.key]
                self.size -= 1

            new_node = Node(key, value)
            self.cache[key] = new_node
            self._add_node(new_node)
            self.size += 1

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the current number of items in the cache."""
        return self.size

    def __contains__(self, key: int) -> bool:
        """Check membership without affecting recency order."""
        return key in self.cache

    def __repr__(self) -> str:
        items = []
        current = self.head.next
        while current is not self.tail:
            items.append(f"{current.key}:{current.value}")
            current = current.next
        order = " → ".join(items) if items else "(empty)"
        return f"LRUCache(capacity={self.capacity}, size={self.size}, order=[{order}])"
