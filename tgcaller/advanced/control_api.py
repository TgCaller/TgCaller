"""
Custom API Handler - Extend TgCaller with custom endpoints
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from aiohttp import web, ClientSession

logger = logging.getLogger(__name__)


class CustomAPIHandler:
    """Custom API endpoints for TgCaller"""
    
    def __init__(self, caller, port: int = 8080):
        self.caller = caller
        self.port = port
        self.app = web.Application()
        self.routes = {}
        self.middleware = []
        self.logger = logger
        self._setup_default_routes()
    
    def _setup_default_routes(self):
        """Setup default API routes"""
        # Status endpoints
        self.app.router.add_get('/status', self._status_handler)
        self.app.router.add_get('/calls', self._calls_handler)
        
        # Control endpoints
        self.app.router.add_post('/join', self._join_handler)
        self.app.router.add_post('/leave', self._leave_handler)
        self.app.router.add_post('/play', self._play_handler)
        self.app.router.add_post('/pause', self._pause_handler)
        self.app.router.add_post('/resume', self._resume_handler)
        self.app.router.add_post('/stop', self._stop_handler)
        self.app.router.add_post('/volume', self._volume_handler)
        
        # Advanced endpoints
        self.app.router.add_get('/stats', self._stats_handler)
        self.app.router.add_post('/webhook', self._webhook_handler)
    
    async def _status_handler(self, request):
        """Get TgCaller status"""
        return web.json_response({
            'status': 'running' if self.caller.is_running else 'stopped',
            'active_calls': len(self.caller.get_active_calls()),
            'version': '1.0.0'
        })
    
    async def _calls_handler(self, request):
        """Get active calls"""
        active_calls = []
        for chat_id in self.caller.get_active_calls():
            active_calls.append({
                'chat_id': chat_id,
                'connected': self.caller.is_connected(chat_id)
            })
        
        return web.json_response({'calls': active_calls})
    
    async def _join_handler(self, request):
        """Join call endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            
            if not chat_id:
                return web.json_response(
                    {'error': 'chat_id required'}, 
                    status=400
                )
            
            success = await self.caller.join_call(chat_id)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _leave_handler(self, request):
        """Leave call endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            
            if not chat_id:
                return web.json_response(
                    {'error': 'chat_id required'}, 
                    status=400
                )
            
            success = await self.caller.leave_call(chat_id)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _play_handler(self, request):
        """Play media endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            source = data.get('source')
            
            if not chat_id or not source:
                return web.json_response(
                    {'error': 'chat_id and source required'}, 
                    status=400
                )
            
            success = await self.caller.play(chat_id, source)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _pause_handler(self, request):
        """Pause endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            
            success = await self.caller.pause(chat_id)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _resume_handler(self, request):
        """Resume endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            
            success = await self.caller.resume(chat_id)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _stop_handler(self, request):
        """Stop endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            
            success = await self.caller.stop(chat_id)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _volume_handler(self, request):
        """Volume control endpoint"""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            volume = data.get('volume')
            
            if volume is None:
                return web.json_response(
                    {'error': 'volume required'}, 
                    status=400
                )
            
            success = await self.caller.set_volume(chat_id, volume)
            return web.json_response({'success': success})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    async def _stats_handler(self, request):
        """Statistics endpoint"""
        return web.json_response({
            'total_calls': len(self.caller.get_active_calls()),
            'uptime': '1h 30m',  # Placeholder
            'memory_usage': '45MB',  # Placeholder
            'cpu_usage': '12%'  # Placeholder
        })
    
    async def _webhook_handler(self, request):
        """Webhook endpoint for external integrations"""
        try:
            data = await request.json()
            event_type = data.get('type')
            
            # Handle different webhook events
            if event_type == 'play_request':
                chat_id = data.get('chat_id')
                source = data.get('source')
                await self.caller.play(chat_id, source)
            
            return web.json_response({'received': True})
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=500
            )
    
    def add_route(
        self, 
        method: str, 
        path: str, 
        handler: Callable
    ):
        """Add custom route"""
        if method.upper() == 'GET':
            self.app.router.add_get(path, handler)
        elif method.upper() == 'POST':
            self.app.router.add_post(path, handler)
        elif method.upper() == 'PUT':
            self.app.router.add_put(path, handler)
        elif method.upper() == 'DELETE':
            self.app.router.add_delete(path, handler)
    
    def add_middleware(self, middleware: Callable):
        """Add middleware"""
        self.app.middlewares.append(middleware)
    
    async def start_server(self):
        """Start API server"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()
            
            self.logger.info(f"Custom API server started on port {self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
    
    async def stop_server(self):
        """Stop API server"""
        # Implementation for stopping server
        self.logger.info("API server stopped")


# Example middleware
async def cors_middleware(request, handler):
    """CORS middleware"""
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


async def auth_middleware(request, handler):
    """Authentication middleware"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return web.json_response(
            {'error': 'Authentication required'}, 
            status=401
        )
    
    # Validate token here
    token = auth_header[7:]  # Remove 'Bearer '
    
    return await handler(request)