"""
Pytest Configuration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_pyrogram_client():
    """Mock Pyrogram client"""
    client = Mock()
    client.is_connected = False
    client.start = AsyncMock(return_value=None)
    client.stop = AsyncMock(return_value=None)
    return client