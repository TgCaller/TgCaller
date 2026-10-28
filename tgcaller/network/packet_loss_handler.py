"""Sequence-based packet-loss statistics; no FEC reconstruction."""


class PacketLossHandler:
    """Measure gaps in a stream of increasing packet sequence IDs."""

    def __init__(self):
        self.reset()

    def observe(self, sequence):
        """Observe a sequence ID and return newly inferred missing count."""
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        if self.last_sequence is None:
            self.first_sequence = sequence
            self.last_sequence = sequence
            self.received_packets = 1
            return 0
        if sequence <= self.last_sequence:
            return 0
        missing = sequence - self.last_sequence - 1
        self.lost_packets += missing
        self.received_packets += 1
        self.last_sequence = sequence
        return missing

    @property
    def loss_rate(self):
        """Estimated loss ratio over the observed sequence range."""
        total = self.received_packets + self.lost_packets
        return self.lost_packets / total if total else 0.0

    def reset(self):
        self.first_sequence = None
        self.last_sequence = None
        self.received_packets = 0
        self.lost_packets = 0
