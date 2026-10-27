import pytest

from tgcaller.utilities import cpu_monitor as cpu_monitor_module


@pytest.mark.asyncio
async def test_start_monitoring_returns_false_without_psutil(monkeypatch):
    monkeypatch.setattr(cpu_monitor_module, "psutil", None)
    monitor = cpu_monitor_module.CpuMonitor()

    assert await monitor.start_monitoring() is False
    assert monitor.monitoring is False
    assert monitor.monitor_task is None


@pytest.mark.asyncio
async def test_collect_stats_returns_none_without_psutil(monkeypatch):
    monkeypatch.setattr(cpu_monitor_module, "psutil", None)
    monitor = cpu_monitor_module.CpuMonitor()

    assert await monitor._collect_stats() is None
