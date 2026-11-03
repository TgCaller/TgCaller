"""Tests that unsupported bridge APIs never claim success or join calls."""

from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.advanced.bridged_calls import BridgedCallManager


@pytest.mark.asyncio
async def test_create_bridge_fails_closed_without_joining_calls():
    caller = Mock()
    caller.is_connected = Mock(return_value=False)
    caller.join_call = AsyncMock()
    manager = BridgedCallManager(caller)

    assert await manager.create_bridge("conference", [101, 202]) is False
    caller.join_call.assert_not_awaited()
    assert manager.list_bridges() == []


@pytest.mark.asyncio
async def test_create_bridge_requires_distinct_chat_ids():
    manager = BridgedCallManager(Mock())

    with pytest.raises(ValueError, match="distinct"):
        await manager.create_bridge("conference", [101, 101])
