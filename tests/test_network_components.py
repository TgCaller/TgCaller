"""Regression tests for the standalone network utility primitives."""

import pytest

from tgcaller.network import (
    BandwidthMonitor,
    JitterBuffer,
    PacketLossHandler,
    RelayNodes,
)


def test_bandwidth_monitor_rolling_rate_and_reset():
    monitor = BandwidthMonitor(window_seconds=10)
    monitor.record(100, timestamp=1)
    monitor.record(50, timestamp=2)
    assert monitor.bytes_per_second(timestamp=2) == 150.0
    monitor.reset()
    assert monitor.bytes_per_second(timestamp=3) == 0.0


def test_bandwidth_monitor_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        BandwidthMonitor(window_seconds=0)
    with pytest.raises(ValueError):
        BandwidthMonitor().record(-1, timestamp=1)


def test_jitter_buffer_orders_and_rejects_duplicates():
    buffer = JitterBuffer(max_size=3)
    assert buffer.push(3, "c")
    assert buffer.push(1, "a")
    assert not buffer.push(1, "duplicate")
    assert buffer.pop_oldest() == (1, "a")
    assert buffer.pop(3) == "c"
    assert len(buffer) == 0


def test_jitter_buffer_is_bounded():
    buffer = JitterBuffer(max_size=2)
    buffer.push(1, "a")
    buffer.push(2, "b")
    buffer.push(3, "c")
    assert len(buffer) == 2
    assert 3 in buffer


def test_packet_loss_handler_counts_gaps_and_ignores_reordering():
    handler = PacketLossHandler()
    assert handler.observe(10) == 0
    assert handler.observe(13) == 2
    assert handler.observe(12) == 0
    assert handler.lost_packets == 2
    assert handler.loss_rate == pytest.approx(2 / 5)
    handler.reset()
    assert handler.loss_rate == 0.0


def test_relay_nodes_deduplicate_and_copy_config():
    config = {"url": "turn:example.invalid", "username": "demo"}
    relays = RelayNodes([config, "turns:example.invalid"])
    assert len(relays) == 2
    assert not relays.add(config)
    returned = relays.get_nodes()
    returned[0]["username"] = "changed"
    assert relays.get_nodes()[0]["username"] == "demo"
    assert relays.remove("turns:example.invalid")
    assert not relays.remove("missing")
