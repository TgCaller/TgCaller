"""Bounded sequence-aware buffer for out-of-order media packets."""
from collections import OrderedDict


class JitterBuffer:
    """Store packets by sequence number and release them in sequence order."""

    def __init__(self, max_size=128):
        if isinstance(max_size, bool) or not isinstance(max_size, int) or max_size < 1:
            raise ValueError("max_size must be a positive integer")
        self.max_size = max_size
        self._packets = OrderedDict()

    def push(self, sequence, packet):
        """Buffer a packet; return False for duplicates or invalid sequence IDs."""
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            return False
        if sequence in self._packets:
            return False
        self._packets[sequence] = packet
        self._packets = OrderedDict(sorted(self._packets.items()))
        while len(self._packets) > self.max_size:
            self._packets.popitem(last=True)
        return True

    def pop(self, sequence):
        """Remove and return a specific packet, or None if unavailable."""
        return self._packets.pop(sequence, None)

    def pop_oldest(self):
        """Return and remove the lowest sequence as a pair, or None."""
        if not self._packets:
            return None
        return self._packets.popitem(last=False)

    def clear(self):
        self._packets.clear()

    def __len__(self):
        return len(self._packets)

    def __contains__(self, sequence):
        return sequence in self._packets
