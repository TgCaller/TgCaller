"""
Pytest Configuration
"""

import pytest
import asyncio
from unittest.mock import Mock


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
    client.start = Mock(return_value=asyncio.coroutine(lambda: None)())
    client.stop = Mock(return_value=asyncio.coroutine(lambda: None)())
    return client