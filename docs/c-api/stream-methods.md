# Stream Methods

## Audio Streaming

### Play Audio File

```c
#include "tgcaller.h"

// Play audio file
int64_t chat_id = -1001234567890;
const char* audio_file = "song.mp3";

TgCallerError error = tgcaller_play(caller, chat_id, audio_file);
if (error == TGCALLER_SUCCESS) {
    printf("Started playing: %s\n", audio_file);
} else {
    fprintf(stderr, "Failed to play audio: %s\n", tgcaller_error_string(error));
}
```

### Play with Configuration

```c
// Create audio configuration
TgCallerAudioConfig audio_config = {
    .bitrate = 128000,
    .sample_rate = 48000,
    .channels = 2,
    .codec = TGCALLER_CODEC_OPUS,
    .noise_suppression = true,
    .echo_cancellation = true
};

// Play with specific configuration
TgCallerError error = tgcaller_play_with_config(
    caller, 
    chat_id, 
    "high_quality_song.flac",
    &audio_config,
    NULL  // No video config
);
```

### Stream from URL

```c
// Stream from HTTP URL
const char* stream_url = "https://example.com/stream.mp3";

TgCallerError error = tgcaller_play(caller, chat_id, stream_url);
if (error == TGCALLER_SUCCESS) {
    printf("Started streaming from URL\n");
} else {
    fprintf(stderr, "Failed to stream from URL: %s\n", tgcaller_error_string(error));
}
```

## Video Streaming

### Play Video File

```c
// Create video configuration
TgCallerVideoConfig video_config = {
    .width = 1280,
    .height = 720,
    .fps = 30,
    .bitrate = 1500000,
    .codec = TGCALLER_CODEC_H264,
    .hardware_acceleration = true
};

// Create audio configuration for video
TgCallerAudioConfig audio_config = {
    .bitrate = 128000,
    .sample_rate = 48000,
    .channels = 2,
    .codec = TGCALLER_CODEC_OPUS
};

// Play video file
TgCallerError error = tgcaller_play_with_config(
    caller,
    chat_id,
    "video.mp4",
    &audio_config,
    &video_config
);

if (error == TGCALLER_SUCCESS) {
    printf("Started playing video\n");
} else {
    fprintf(stderr, "Failed to play video: %s\n", tgcaller_error_string(error));
}
```

## Stream Control

### Pause Stream

```c
// Pause current stream
TgCallerError error = tgcaller_pause(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Stream paused\n");
} else {
    fprintf(stderr, "Failed to pause stream: %s\n", tgcaller_error_string(error));
}
```

### Resume Stream

```c
// Resume paused stream
TgCallerError error = tgcaller_resume(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Stream resumed\n");
} else {
    fprintf(stderr, "Failed to resume stream: %s\n", tgcaller_error_string(error));
}
```

### Stop Stream

```c
// Stop current stream
TgCallerError error = tgcaller_stop_stream(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Stream stopped\n");
} else {
    fprintf(stderr, "Failed to stop stream: %s\n", tgcaller_error_string(error));
}
```

### Volume Control

```c
// Set volume (0.0 to 1.0)
float volume = 0.8f;  // 80%

TgCallerError error = tgcaller_set_volume(caller, chat_id, volume);
if (error == TGCALLER_SUCCESS) {
    printf("Volume set to %.0f%%\n", volume * 100);
} else {
    fprintf(stderr, "Failed to set volume: %s\n", tgcaller_error_string(error));
}

// Get current volume
float current_volume;
error = tgcaller_get_volume(caller, chat_id, &current_volume);
if (error == TGCALLER_SUCCESS) {
    printf("Current volume: %.0f%%\n", current_volume * 100);
}
```

### Seek Control

```c
// Seek to position (in seconds)
double position = 60.0;  // 1 minute

TgCallerError error = tgcaller_seek(caller, chat_id, position);
if (error == TGCALLER_SUCCESS) {
    printf("Seeked to %.1f seconds\n", position);
} else {
    fprintf(stderr, "Failed to seek: %s\n", tgcaller_error_string(error));
}

// Get current position
double current_position;
error = tgcaller_get_position(caller, chat_id, &current_position);
if (error == TGCALLER_SUCCESS) {
    printf("Current position: %.1f seconds\n", current_position);
}
```

## Stream Information

### Get Stream Status

```c
// Get current stream status
TgCallerStreamStatus status;
TgCallerError error = tgcaller_get_stream_status(caller, chat_id, &status);

if (error == TGCALLER_SUCCESS) {
    switch (status) {
        case TGCALLER_STREAM_IDLE:
            printf("No active stream\n");
            break;
        case TGCALLER_STREAM_PLAYING:
            printf("Stream is playing\n");
            break;
        case TGCALLER_STREAM_PAUSED:
            printf("Stream is paused\n");
            break;
        case TGCALLER_STREAM_STOPPED:
            printf("Stream is stopped\n");
            break;
        default:
            printf("Unknown stream status\n");
            break;
    }
} else {
    fprintf(stderr, "Failed to get stream status: %s\n", tgcaller_error_string(error));
}
```

### Get Stream Information

```c
// Get detailed stream information
TgCallerStreamInfo stream_info;
TgCallerError error = tgcaller_get_stream_info(caller, chat_id, &stream_info);

if (error == TGCALLER_SUCCESS) {
    printf("Stream Information:\n");
    printf("  Source: %s\n", stream_info.source);
    printf("  Duration: %.1f seconds\n", stream_info.duration);
    printf("  Position: %.1f seconds\n", stream_info.position);
    printf("  Volume: %.0f%%\n", stream_info.volume * 100);
    printf("  Has Video: %s\n", stream_info.has_video ? "Yes" : "No");
    
    if (stream_info.has_video) {
        printf("  Video: %dx%d @ %d fps\n", 
               stream_info.video_width, 
               stream_info.video_height, 
               stream_info.video_fps);
    }
    
    printf("  Audio: %d Hz, %d channels, %d kbps\n",
           stream_info.audio_sample_rate,
           stream_info.audio_channels,
           stream_info.audio_bitrate / 1000);
} else {
    fprintf(stderr, "Failed to get stream info: %s\n", tgcaller_error_string(error));
}
```

## Advanced Streaming

### Queue Management

```c
// Add to queue
TgCallerError error = tgcaller_queue_add(caller, chat_id, "song1.mp3");
if (error == TGCALLER_SUCCESS) {
    printf("Added to queue\n");
}

// Get queue size
size_t queue_size;
error = tgcaller_queue_size(caller, chat_id, &queue_size);
if (error == TGCALLER_SUCCESS) {
    printf("Queue size: %zu\n", queue_size);
}

// Skip to next in queue
error = tgcaller_queue_next(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Skipped to next in queue\n");
}

// Clear queue
error = tgcaller_queue_clear(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Queue cleared\n");
}
```

### Repeat Mode

```c
// Set repeat mode
TgCallerRepeatMode repeat_mode = TGCALLER_REPEAT_ONE;

TgCallerError error = tgcaller_set_repeat_mode(caller, chat_id, repeat_mode);
if (error == TGCALLER_SUCCESS) {
    printf("Repeat mode set\n");
}

// Available repeat modes:
// TGCALLER_REPEAT_NONE - No repeat
// TGCALLER_REPEAT_ONE  - Repeat current track
// TGCALLER_REPEAT_ALL  - Repeat all tracks in queue
```

### Stream from Memory

```c
// Stream from memory buffer
const uint8_t* audio_data = /* your audio data */;
size_t data_size = /* size of audio data */;

TgCallerMemoryStream memory_stream = {
    .data = audio_data,
    .size = data_size,
    .format = TGCALLER_FORMAT_PCM,
    .sample_rate = 48000,
    .channels = 2,
    .bits_per_sample = 16
};

TgCallerError error = tgcaller_play_memory(caller, chat_id, &memory_stream);
if (error == TGCALLER_SUCCESS) {
    printf("Started playing from memory\n");
} else {
    fprintf(stderr, "Failed to play from memory: %s\n", tgcaller_error_string(error));
}
```

## Complete Streaming Example

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "tgcaller.h"

void stream_callback(TgCallerStreamEvent event, void* user_data) {
    int64_t chat_id = *(int64_t*)user_data;
    
    switch (event.type) {
        case TGCALLER_STREAM_STARTED:
            printf("Stream started in chat %lld\n", chat_id);
            break;
        case TGCALLER_STREAM_ENDED:
            printf("Stream ended in chat %lld\n", chat_id);
            break;
        case TGCALLER_STREAM_ERROR:
            printf("Stream error in chat %lld: %s\n", chat_id, event.error_message);
            break;
    }
}

int main() {
    TgCaller* caller = tgcaller_create();
    if (!caller) return -1;
    
    // Setup credentials and start
    tgcaller_set_credentials(caller, 12345, "api_hash");
    tgcaller_start(caller);
    
    int64_t chat_id = -1001234567890;
    
    // Register stream callback
    tgcaller_set_stream_callback(caller, stream_callback, &chat_id);
    
    // Join call
    tgcaller_join_call(caller, chat_id);
    
    // Play audio file
    tgcaller_play(caller, chat_id, "song.mp3");
    
    // Wait for stream to finish
    sleep(30);
    
    // Control stream
    tgcaller_set_volume(caller, chat_id, 0.5f);  // 50% volume
    tgcaller_pause(caller, chat_id);
    sleep(2);
    tgcaller_resume(caller, chat_id);
    
    // Cleanup
    tgcaller_leave_call(caller, chat_id);
    tgcaller_stop(caller);
    tgcaller_destroy(caller);
    
    return 0;
}
```