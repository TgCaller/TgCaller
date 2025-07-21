# Advanced Features

TgCaller provides powerful advanced features for professional applications and complex use cases.

## YouTube Integration

Stream YouTube videos directly in your calls without downloading.

### Basic YouTube Streaming

```python
from tgcaller.advanced import YouTubeStreamer

youtube = YouTubeStreamer(caller)

# Play YouTube video directly
await youtube.play_youtube_url(chat_id, "https://youtube.com/watch?v=...")

# Search and play first result
await youtube.search_and_play(chat_id, "relaxing music", index=0)
```

### YouTube Download and Play

```python
from tgcaller.advanced import YouTubeDownloader

downloader = YouTubeDownloader()

# Download and play
file_path = await downloader.download_video(
    "https://youtube.com/watch?v=...", 
    quality='best[height<=720]'
)
await caller.play(chat_id, file_path)
```

## Screen Sharing

Share your screen or specific application windows in video calls.

### Full Screen Sharing

```python
from tgcaller.advanced import ScreenShareStreamer

screen_streamer = ScreenShareStreamer(caller, chat_id)

# Start screen sharing (monitor 1)
await screen_streamer.start_streaming(monitor_index=1)

# Stop screen sharing
await screen_streamer.stop_streaming()
```

### Region Sharing

```python
# Share specific screen region
region = (100, 100, 800, 600)  # x, y, width, height
await screen_streamer.start_streaming(region=region)
```

### List Available Monitors

```python
from tgcaller.advanced import ScreenShare

screen_share = ScreenShare()
monitors = screen_share.list_monitors()

for monitor in monitors:
    print(f"Monitor {monitor['index']}: {monitor['width']}x{monitor['height']}")
```

## Microphone Streaming

Stream live microphone input to calls.

### Basic Microphone Streaming

```python
from tgcaller.advanced import MicrophoneStreamer

mic_streamer = MicrophoneStreamer(caller, chat_id)

# Start microphone streaming
await mic_streamer.start_streaming()

# Stop microphone streaming
await mic_streamer.stop_streaming()
```

### Advanced Microphone Configuration

```python
from tgcaller import AudioConfig

# High-quality microphone config
audio_config = AudioConfig(
    bitrate=128000,
    sample_rate=48000,
    channels=1,  # Mono for microphone
    noise_suppression=True,
    echo_cancellation=True
)

await mic_streamer.start_streaming(
    audio_config=audio_config,
    device_index=0  # Specific microphone device
)
```

## Speech Transcription

Real-time speech-to-text using OpenAI Whisper.

### Basic Transcription

```python
from tgcaller.advanced import WhisperTranscription

# Initialize transcriber
transcriber = WhisperTranscription("base")

# Add callback for transcription results
@transcriber.add_callback
def on_transcription(result):
    print(f"Transcribed: {result['text']}")
    print(f"Language: {result['language']}")
    print(f"Confidence: {result['confidence']:.2%}")

# Start real-time transcription
await transcriber.start_transcription()
```

### File Transcription

```python
# Transcribe audio file
result = await transcriber.transcribe_file("speech.wav")

print(f"Text: {result['text']}")
print(f"Language: {result['language']}")
print(f"Duration: {result['duration']:.1f} seconds")
```

### Transcription Manager

```python
from tgcaller.advanced import TranscriptionManager

# Manage transcription for multiple calls
transcription_manager = TranscriptionManager(caller)

# Start transcription for specific call
await transcription_manager.start_transcription_for_call(
    chat_id, 
    model_name="base", 
    language="en"
)

# Stop transcription
await transcription_manager.stop_transcription_for_call(chat_id)
```

## Audio and Video Filters

Apply real-time effects to audio and video streams.

### Audio Filters

```python
from tgcaller.advanced import AudioFilters, FilterChain

audio_filters = AudioFilters()
filter_chain = FilterChain()

# Add echo effect
filter_chain.add_audio_filter(
    audio_filters.apply_echo,
    delay=0.3,
    decay=0.5
)

# Add reverb effect
filter_chain.add_audio_filter(
    audio_filters.apply_reverb,
    room_size=0.7,
    damping=0.4
)

# Process audio through filters
filtered_audio = filter_chain.process_audio(audio_data)
```

### Video Filters

```python
from tgcaller.advanced import VideoFilters

video_filters = VideoFilters()

# Apply blur effect
blurred_frame = video_filters.apply_blur(video_frame, kernel_size=15)

# Apply sepia effect
sepia_frame = video_filters.apply_sepia(video_frame)

# Apply cartoon effect
cartoon_frame = video_filters.apply_cartoon(video_frame)
```

### Filter Chain for Video

```python
filter_chain = FilterChain()

# Add multiple video filters
filter_chain.add_video_filter(video_filters.apply_blur, kernel_size=5)
filter_chain.add_video_filter(video_filters.apply_sepia)

# Process video through filter chain
filtered_video = filter_chain.process_video(video_frame)
```

## Bridged Calls

Connect multiple chats for conference calls.

### Create Bridge

```python
from tgcaller.advanced import BridgedCallManager

bridge_manager = BridgedCallManager(caller)

# Create bridge between multiple chats
chat_ids = [-1001234567890, -1009876543210, -1001122334455]
await bridge_manager.create_bridge("conference", chat_ids)
```

### Manage Bridge

```python
# Add chat to existing bridge
await bridge_manager.add_chat_to_bridge("conference", new_chat_id)

# Remove chat from bridge
await bridge_manager.remove_chat_from_bridge("conference", chat_id)

# Destroy bridge
await bridge_manager.destroy_bridge("conference")
```

## Custom API Server

Extend TgCaller with REST API endpoints.

### Basic API Server

```python
from tgcaller.advanced import CustomAPIHandler

# Create API handler
api = CustomAPIHandler(caller, port=8080)

# Add custom route
@api.add_route('GET', '/status')
async def custom_status(request):
    return web.json_response({
        'status': 'running',
        'active_calls': len(caller.get_active_calls())
    })

# Start server
await api.start_server()
```

### API Endpoints

The custom API provides these default endpoints:

- `GET /status` - Get TgCaller status
- `GET /calls` - List active calls
- `POST /join` - Join call
- `POST /leave` - Leave call
- `POST /play` - Play media
- `POST /pause` - Pause stream
- `POST /resume` - Resume stream
- `POST /volume` - Set volume

### Example API Usage

```bash
# Join call via API
curl -X POST http://localhost:8080/join \
  -H "Content-Type: application/json" \
  -d '{"chat_id": -1001234567890}'

# Play media via API
curl -X POST http://localhost:8080/play \
  -H "Content-Type: application/json" \
  -d '{"chat_id": -1001234567890, "source": "song.mp3"}'
```

## Multiple Client Management

Manage multiple Telegram accounts simultaneously.

### Multi-Client Setup

```python
from tgcaller.advanced import MultiClientManager

# Create multiple clients
clients = [
    Client(f"session_{i}", api_id=API_ID, api_hash=API_HASH)
    for i in range(3)
]

# Create multi-client manager
multi_manager = MultiClientManager(clients)

# Start all clients
await multi_manager.start_all()

# Join calls with different clients
await multi_manager.join_call(0, chat_id_1)  # Client 0
await multi_manager.join_call(1, chat_id_2)  # Client 1
await multi_manager.join_call(2, chat_id_3)  # Client 2
```

## Raw Streaming

For advanced users who need direct control over media streams.

### Raw Audio Streaming

```python
from tgcaller.advanced import RawStreamer
import numpy as np

raw_streamer = RawStreamer(caller, chat_id)

# Generate raw audio data
sample_rate = 48000
duration = 5  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))
audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

# Stream raw audio
await raw_streamer.stream_audio(audio_data, sample_rate)
```

### Raw Video Streaming

```python
import cv2

# Generate raw video frames
for i in range(300):  # 10 seconds at 30 FPS
    # Create a frame (example: gradient)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[:, :, 0] = i % 255  # Red channel
    
    # Stream frame
    await raw_streamer.stream_video_frame(frame)
    await asyncio.sleep(1/30)  # 30 FPS
```

## Performance Optimization

### Memory Management

```python
# Configure memory limits for advanced features
from tgcaller.advanced import PerformanceConfig

config = PerformanceConfig(
    max_buffer_size=1024 * 1024,  # 1MB buffer
    enable_gpu_acceleration=True,
    thread_pool_size=4
)

caller.set_performance_config(config)
```

### Async Processing

```python
# Process multiple streams concurrently
async def process_multiple_streams():
    tasks = [
        caller.play(chat_id_1, "audio1.mp3"),
        caller.play(chat_id_2, "audio2.mp3"),
        caller.play(chat_id_3, "audio3.mp3")
    ]
    
    await asyncio.gather(*tasks)
```

These advanced features enable you to build sophisticated applications with TgCaller, from simple music bots to complex conference systems with real-time processing capabilities.

## FastStreamBuffer - Ultra-Low-Latency Streaming

FastStreamBuffer provides ultra-low-latency streaming capabilities with async buffered chunks.

### Basic Usage

```python
from tgcaller.streaming import FastStreamBuffer, BufferConfig
from tgcaller.advanced import AdvancedYouTubeStreamer

# Create buffer manager
buffer_manager = BufferManager(max_buffers=10)

# Create advanced YouTube streamer
youtube_streamer = AdvancedYouTubeStreamer(caller, buffer_manager)

# Stream with ultra-low latency
await youtube_streamer.stream_youtube_ultra_low_latency(
    chat_id, 
    "https://youtube.com/watch?v=...",
    quality="720p"
)
```

### Custom Buffer Configuration

```python
from tgcaller.streaming import BufferConfig

# Ultra-low-latency configuration
config = BufferConfig(
    max_buffer_size=30,
    min_buffer_size=5,
    target_buffer_size=15,
    chunk_duration_ms=10.0,  # 10ms chunks
    max_latency_ms=50.0,     # 50ms max latency
    adaptive_quality=True,
    use_threading=True
)

buffer = FastStreamBuffer(config)
```

### Performance Monitoring

```python
# Get streaming statistics
stats = youtube_streamer.get_stream_stats(chat_id)
print(f"Latency: {stats['avg_latency_ms']:.1f}ms")
print(f"Buffer Health: {stats['health_percent']:.1f}%")
print(f"Throughput: {stats['throughput_mbps']:.2f} Mbps")

# Get buffer manager statistics
global_stats = buffer_manager.get_global_stats()
print(f"Total Buffers: {global_stats.total_buffers}")
print(f"Average Health: {global_stats.avg_health:.1f}%")
```

### Advanced Features

- **Adaptive Quality Control**: Automatically adjusts quality based on network conditions
- **Buffer Optimization**: Real-time buffer size and latency optimization
- **Hardware Acceleration**: Uses GPU acceleration when available
- **Multi-Stream Management**: Handle multiple concurrent streams efficiently
- **Performance Monitoring**: Real-time performance metrics and alerts