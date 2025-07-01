# 🔌 Plugin Development Guide

TgCaller supports a powerful plugin system that allows you to extend functionality with custom features.

## Creating a Plugin

### Basic Plugin Structure

```python
from tgcaller.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom plugin"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.enabled = True
    
    async def on_load(self):
        """Called when plugin is loaded"""
        print(f"Loading {self.name} plugin...")
    
    async def on_unload(self):
        """Called when plugin is unloaded"""
        print(f"Unloading {self.name} plugin...")
```

### Audio Processing Plugin

```python
from tgcaller.plugins import BasePlugin
import numpy as np

class VoiceEffectsPlugin(BasePlugin):
    name = "voice_effects"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.effects = config.get('effects', []) if config else []
    
    async def process_audio(self, audio_frame):
        """Process audio frame"""
        if 'robot' in self.effects:
            audio_frame = self.apply_robot_effect(audio_frame)
        
        if 'echo' in self.effects:
            audio_frame = self.apply_echo_effect(audio_frame)
        
        return audio_frame
    
    def apply_robot_effect(self, audio_frame):
        """Apply robot voice effect"""
        # Simple pitch shifting
        return audio_frame * 0.8
    
    def apply_echo_effect(self, audio_frame):
        """Apply echo effect"""
        # Simple echo implementation
        echo_delay = int(0.3 * 48000)  # 300ms delay
        echo_frame = np.zeros_like(audio_frame)
        
        if len(audio_frame) > echo_delay:
            echo_frame[echo_delay:] = audio_frame[:-echo_delay] * 0.3
            return audio_frame + echo_frame
        
        return audio_frame
```

### Video Processing Plugin

```python
import cv2
from tgcaller.plugins import BasePlugin

class VideoFiltersPlugin(BasePlugin):
    name = "video_filters"
    
    async def process_video(self, video_frame):
        """Process video frame"""
        if self.config.get('blur'):
            video_frame = cv2.GaussianBlur(video_frame, (15, 15), 0)
        
        if self.config.get('grayscale'):
            video_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2GRAY)
            video_frame = cv2.cvtColor(video_frame, cv2.COLOR_GRAY2BGR)
        
        if self.config.get('sepia'):
            video_frame = self.apply_sepia(video_frame)
        
        return video_frame
    
    def apply_sepia(self, frame):
        """Apply sepia effect"""
        sepia_filter = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ])
        
        sepia_frame = frame.dot(sepia_filter.T)
        sepia_frame = np.clip(sepia_frame, 0, 255)
        return sepia_frame.astype(np.uint8)
```

### Event Handler Plugin

```python
from tgcaller.plugins import BasePlugin

class LoggingPlugin(BasePlugin):
    name = "logging"
    
    async def on_stream_start(self, chat_id, source):
        """Called when stream starts"""
        self.logger.info(f"Stream started in {chat_id}: {source}")
    
    async def on_stream_end(self, chat_id):
        """Called when stream ends"""
        self.logger.info(f"Stream ended in {chat_id}")
    
    async def on_user_joined(self, chat_id, user_id):
        """Called when user joins call"""
        self.logger.info(f"User {user_id} joined call in {chat_id}")
    
    async def on_user_left(self, chat_id, user_id):
        """Called when user leaves call"""
        self.logger.info(f"User {user_id} left call in {chat_id}")
```

## Plugin Registration

### Register Plugin with TgCaller

```python
from tgcaller import TgCaller

# Create TgCaller instance
caller = TgCaller(app)

# Register plugins
voice_effects = VoiceEffectsPlugin({
    'effects': ['robot', 'echo']
})
caller.register_plugin(voice_effects)

video_filters = VideoFiltersPlugin({
    'blur': True,
    'sepia': False
})
caller.register_plugin(video_filters)

logging_plugin = LoggingPlugin()
caller.register_plugin(logging_plugin)
```

### Plugin Configuration

```python
# Plugin with configuration
plugin_config = {
    'enabled': True,
    'priority': 10,
    'settings': {
        'effect_strength': 0.8,
        'buffer_size': 1024
    }
}

plugin = MyPlugin(plugin_config)
caller.register_plugin(plugin)
```

## Advanced Plugin Features

### Plugin Dependencies

```python
class AdvancedPlugin(BasePlugin):
    name = "advanced_plugin"
    dependencies = ["voice_effects", "logging"]
    
    async def on_load(self):
        # Check if dependencies are loaded
        for dep in self.dependencies:
            if not self.caller.is_plugin_loaded(dep):
                raise PluginError(f"Dependency {dep} not found")
```

### Plugin Communication

```python
class PluginA(BasePlugin):
    name = "plugin_a"
    
    async def send_message_to_plugin(self, plugin_name, message):
        """Send message to another plugin"""
        await self.caller.send_plugin_message(plugin_name, message)

class PluginB(BasePlugin):
    name = "plugin_b"
    
    async def on_plugin_message(self, sender, message):
        """Receive message from another plugin"""
        print(f"Received from {sender}: {message}")
```

### Plugin Storage

```python
class DataPlugin(BasePlugin):
    name = "data_plugin"
    
    async def save_data(self, key, value):
        """Save plugin data"""
        await self.storage.set(key, value)
    
    async def load_data(self, key):
        """Load plugin data"""
        return await self.storage.get(key)
    
    async def on_stream_start(self, chat_id, source):
        # Save stream history
        history = await self.load_data('stream_history') or []
        history.append({
            'chat_id': chat_id,
            'source': source,
            'timestamp': time.time()
        })
        await self.save_data('stream_history', history)
```

## Plugin Examples

### Music Queue Plugin

```python
from collections import deque
from tgcaller.plugins import BasePlugin

class MusicQueuePlugin(BasePlugin):
    name = "music_queue"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.queues = {}  # chat_id -> deque
    
    def add_to_queue(self, chat_id, song):
        """Add song to queue"""
        if chat_id not in self.queues:
            self.queues[chat_id] = deque()
        
        self.queues[chat_id].append(song)
    
    def get_next_song(self, chat_id):
        """Get next song from queue"""
        if chat_id in self.queues and self.queues[chat_id]:
            return self.queues[chat_id].popleft()
        return None
    
    async def on_stream_end(self, chat_id):
        """Auto-play next song"""
        next_song = self.get_next_song(chat_id)
        if next_song:
            await self.caller.play(chat_id, next_song)
```

### Auto-Moderator Plugin

```python
class AutoModeratorPlugin(BasePlugin):
    name = "auto_moderator"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.max_users = config.get('max_users', 50) if config else 50
        self.banned_users = set(config.get('banned_users', [])) if config else set()
    
    async def on_user_joined(self, chat_id, user_id):
        """Check user when they join"""
        # Check if user is banned
        if user_id in self.banned_users:
            await self.caller.kick_user(chat_id, user_id)
            return
        
        # Check user limit
        active_users = await self.caller.get_call_participants(chat_id)
        if len(active_users) > self.max_users:
            await self.caller.kick_user(chat_id, user_id)
```

### Statistics Plugin

```python
import time
from tgcaller.plugins import BasePlugin

class StatisticsPlugin(BasePlugin):
    name = "statistics"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.stats = {
            'total_calls': 0,
            'total_duration': 0,
            'streams_played': 0,
            'users_served': set()
        }
        self.call_start_times = {}
    
    async def on_call_start(self, chat_id):
        """Track call start"""
        self.stats['total_calls'] += 1
        self.call_start_times[chat_id] = time.time()
    
    async def on_call_end(self, chat_id):
        """Track call end"""
        if chat_id in self.call_start_times:
            duration = time.time() - self.call_start_times[chat_id]
            self.stats['total_duration'] += duration
            del self.call_start_times[chat_id]
    
    async def on_stream_start(self, chat_id, source):
        """Track stream"""
        self.stats['streams_played'] += 1
    
    async def on_user_joined(self, chat_id, user_id):
        """Track unique users"""
        self.stats['users_served'].add(user_id)
    
    def get_statistics(self):
        """Get current statistics"""
        stats = self.stats.copy()
        stats['unique_users'] = len(self.stats['users_served'])
        stats['average_call_duration'] = (
            self.stats['total_duration'] / max(self.stats['total_calls'], 1)
        )
        return stats
```

## Plugin Best Practices

### 1. Error Handling

```python
class SafePlugin(BasePlugin):
    async def process_audio(self, audio_frame):
        try:
            # Your processing code
            return processed_frame
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            return audio_frame  # Return original on error
```

### 2. Performance Optimization

```python
class OptimizedPlugin(BasePlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self.buffer_pool = []  # Reuse buffers
        self.cache = {}  # Cache expensive operations
    
    async def process_audio(self, audio_frame):
        # Use object pooling for better performance
        buffer = self.get_buffer()
        try:
            # Process audio
            return processed_frame
        finally:
            self.return_buffer(buffer)
```

### 3. Configuration Validation

```python
class ConfigurablePlugin(BasePlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self.validate_config()
    
    def validate_config(self):
        """Validate plugin configuration"""
        if self.config:
            if 'required_setting' not in self.config:
                raise ValueError("required_setting is missing")
            
            if not isinstance(self.config['required_setting'], int):
                raise TypeError("required_setting must be an integer")
```

### 4. Resource Cleanup

```python
class ResourcePlugin(BasePlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self.resources = []
    
    async def on_load(self):
        # Initialize resources
        self.resources.append(SomeResource())
    
    async def on_unload(self):
        # Cleanup resources
        for resource in self.resources:
            await resource.cleanup()
        self.resources.clear()
```

## Plugin Testing

```python
import pytest
from unittest.mock import Mock
from tgcaller.plugins import BasePlugin

class TestMyPlugin:
    @pytest.fixture
    def plugin(self):
        config = {'test_setting': True}
        return MyPlugin(config)
    
    @pytest.mark.asyncio
    async def test_audio_processing(self, plugin):
        # Test audio processing
        input_frame = np.random.random(1024)
        output_frame = await plugin.process_audio(input_frame)
        
        assert output_frame is not None
        assert len(output_frame) == len(input_frame)
    
    def test_configuration(self, plugin):
        # Test configuration
        assert plugin.config['test_setting'] is True
```

This plugin system allows you to extend TgCaller with custom functionality while maintaining clean separation of concerns and easy testing.