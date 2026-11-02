"""TgCaller client shutdown regression tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.client import TgCaller


@pytest.mark.asyncio
async def test_stop_closes_custom_api_even_when_call_service_is_not_running():
    caller = object.__new__(TgCaller)
    caller._is_connected = False
    caller._logger = Mock()
    caller._custom_api_server = Mock()
    caller._custom_api_server.stop = AsyncMock()

    await caller.stop()

    caller._custom_api_server.stop.assert_awaited_once()
