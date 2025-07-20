"""
Test Custom API System
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from tgcaller.api import CustomAPIServer


class TestCustomAPIServer(AioHTTPTestCase):
    """Test Custom API Server"""
    
    async def get_application(self):
        """Create test application"""
        # Mock caller
        self.mock_caller = Mock()
        self.mock_caller.client = Mock()
        self.mock_caller.is_running = True
        
        # Create API server
        self.api_server = CustomAPIServer(self.mock_caller, "localhost", 8080)
        return self.api_server.app
    
    @unittest_run_loop
    async def test_health_check(self):
        """Test health check endpoint"""
        resp = await self.client.request("GET", "/health")
        self.assertEqual(resp.status, 200)
        
        data = await resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "TgCaller Custom API")
        self.assertTrue(data["caller_running"])
    
    @unittest_run_loop
    async def test_no_handler_error(self):
        """Test error when no handler is registered"""
        resp = await self.client.request("POST", "/", json={"test": "data"})
        self.assertEqual(resp.status, 400)
        
        data = await resp.json()
        self.assertEqual(data["error"], "NO_CUSTOM_API_DECORATOR")
    
    @unittest_run_loop
    async def test_invalid_json_error(self):
        """Test error for invalid JSON"""
        resp = await self.client.request("POST", "/", data="invalid json")
        self.assertEqual(resp.status, 400)
        
        data = await resp.json()
        self.assertEqual(data["error"], "INVALID_JSON_FORMAT_REQUEST")
    
    @unittest_run_loop
    async def test_custom_handler(self):
        """Test custom handler execution"""
        # Register handler
        async def test_handler(client, data):
            return {"message": "success", "received": data}
        
        self.api_server.set_custom_handler(test_handler)
        
        # Test request
        test_data = {"action": "test", "value": 123}
        resp = await self.client.request("POST", "/", json=test_data)
        self.assertEqual(resp.status, 200)
        
        data = await resp.json()
        self.assertEqual(data["message"], "success")
        self.assertEqual(data["received"], test_data)
    
    @unittest_run_loop
    async def test_handler_error(self):
        """Test handler error handling"""
        # Register handler that raises error
        async def error_handler(client, data):
            raise ValueError("Test error")
        
        self.api_server.set_custom_handler(error_handler)
        
        # Test request
        resp = await self.client.request("POST", "/", json={"test": "data"})
        self.assertEqual(resp.status, 500)
        
        data = await resp.json()
        self.assertEqual(data["error"], "HANDLER_ERROR")
        self.assertIn("Test error", data["message"])
    
    @unittest_run_loop
    async def test_options_request(self):
        """Test CORS preflight request"""
        resp = await self.client.request("OPTIONS", "/")
        self.assertEqual(resp.status, 200)
        
        headers = resp.headers
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        self.assertIn("POST", headers["Access-Control-Allow-Methods"])