"""Regression tests for the advanced aiohttp control API."""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.advanced.control_api import CustomAPIHandler


@pytest.mark.asyncio
async def test_stop_endpoint_calls_stream_stop_not_client_shutdown():
    caller = Mock()
    caller.stop_stream = AsyncMock(return_value=True)
    handler = CustomAPIHandler(caller)
    request = Mock()
    request.json = AsyncMock(return_value={"chat_id": -1001234567890})

    response = await handler._stop_handler(request)

    assert response.status == 200
    assert json.loads(response.text) == {"success": True}
    caller.stop_stream.assert_awaited_once_with(-1001234567890)
    caller.stop.assert_not_called()
