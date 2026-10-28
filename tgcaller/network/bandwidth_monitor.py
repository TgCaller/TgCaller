"""Rolling bandwidth measurements for media traffic."""
from collections import deque
from time import monotonic


class BandwidthMonitor:
    """Track transferred bytes over a rolling time window."""

    def __init__(self, window_seconds=10.0):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")
        self.window_seconds = float(window_seconds)
        self._samples = deque()
        self._total_bytes = 0

    def record(self, byte_count, timestamp=None):
        """Record a transfer at an optional monotonic timestamp."""
        if isinstance(byte_count, bool) or not isinstance(byte_count, int):
            raise TypeError("byte_count must be an integer")
        if byte_count < 0:
            raise ValueError("byte_count cannot be negative")
        now = monotonic() if timestamp is None else float(timestamp)
        self._samples.append((now, byte_count))
        self._total_bytes += byte_count
        self._expire(now)

    def _expire(self, now):
        cutoff = now - self.window_seconds
        while self._samples and self._samples[0][0] < cutoff:
            _, size = self._samples.popleft()
            self._total_bytes -= size

    def bytes_per_second(self, timestamp=None):
        """Return the rolling average in bytes per second."""
        now = monotonic() if timestamp is None else float(timestamp)
        self._expire(now)
        if not self._samples:
            return 0.0
        elapsed = min(self.window_seconds, max(0.0, now - self._samples[0][0]))
        return float(self._total_bytes) if elapsed == 0 else self._total_bytes / elapsed

    @property
    def total_bytes(self):
        self._expire(monotonic())
        return self._total_bytes

    def reset(self):
        self._samples.clear()
        self._total_bytes = 0
