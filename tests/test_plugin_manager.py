"""Plugin manager dependency and cleanup regression tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.plugins import BasePlugin, PluginManager


class _Plugin(BasePlugin):
    def __init__(self, name, dependencies=()):
        self.name = name
        self.dependencies = tuple(dependencies)
        super().__init__()


@pytest.mark.asyncio
async def test_cleanup_unloads_dependents_before_their_dependencies():
    manager = PluginManager(Mock())
    dependency = _Plugin("dependency")
    dependent = _Plugin("dependent", dependencies=("dependency",))
    dependency.on_unload = AsyncMock()
    dependent.on_unload = AsyncMock()

    await manager.register_plugin(dependency)
    await manager.register_plugin(dependent)
    await manager.cleanup()

    dependent.on_unload.assert_awaited_once()
    dependency.on_unload.assert_awaited_once()
    assert manager.get_loaded_plugins() == []


@pytest.mark.asyncio
async def test_register_rejects_missing_plugin_dependency():
    manager = PluginManager(Mock())
    plugin = _Plugin("dependent", dependencies=("missing",))

    with pytest.raises(ValueError, match="dependency"):
        await manager.register_plugin(plugin)

    assert manager.get_loaded_plugins() == []
