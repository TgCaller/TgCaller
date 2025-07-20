"""
Custom HTTP API Server for External Control
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
from aiohttp import web, ClientSession
from aiohttp.web_response import Response

logger = logging.getLogger(__name__)


class CustomAPIServer:
    """HTTP API Server for external TgCaller control"""
    
    def __init__(self, caller, host: str = "localhost", port: int = 8080):
        """
        Initialize Custom API Server
        
        Args:
            caller: TgCaller instance
            host: Server host
            port: Server port
        """
        self.caller = caller
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.custom_handler: Optional[Callable] = None
        self.logger = logger
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        self.app.router.add_post('/', self._handle_custom_request)
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_options('/', self._handle_options)
    
    def set_custom_handler(self, handler: Callable):
        """Set custom request handler"""
        self.custom_handler = handler
    
    async def _handle_custom_request(self, request) -> Response:
        """Handle custom API requests"""
        try:
            # Check if handler is registered
            if not self.custom_handler:
                return web.json_response(
                    {"error": "NO_CUSTOM_API_DECORATOR"},
                    status=400
                )
            
            # Parse JSON
            try:
                data = await request.json()
            except (json.JSONDecodeError, ValueError):
                return web.json_response(
                    {"error": "INVALID_JSON_FORMAT_REQUEST"},
                    status=400
                )
            
            # Call custom handler
            try:
                result = await self.custom_handler(self.caller.client, data)
                
                # Ensure result is JSON serializable
                if result is None:
                    result = {"status": "success"}
                elif not isinstance(result, dict):
                    result = {"result": result}
                
                return web.json_response(result)
                
            except Exception as e:
                self.logger.error(f"Error in custom handler: {e}")
                return web.json_response(
                    {"error": "HANDLER_ERROR", "message": str(e)},
                    status=500
                )
                
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return web.json_response(
                {"error": "INTERNAL_ERROR", "message": str(e)},
                status=500
            )
    
    async def _health_check(self, request) -> Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "service": "TgCaller Custom API",
            "caller_running": self.caller.is_running if self.caller else False
        })
    
    async def _handle_options(self, request) -> Response:
        """Handle CORS preflight requests"""
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
    
    async def start(self):
        """Start the API server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            self.logger.info(f"Custom API server started on {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            raise
    
    async def stop(self):
        """Stop the API server"""
        try:
            if self.site:
                await self.site.stop()
                self.site = None
            
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
            
            self.logger.info("Custom API server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping API server: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.runner is not None and self.site is not None