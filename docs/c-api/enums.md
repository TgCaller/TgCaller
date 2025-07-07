# Available Enums

## Error Codes

### TgCallerError

```c
typedef enum {
    TGCALLER_SUCCESS = 0,                    // Operation successful
    TGCALLER_ERROR_INVALID_PARAMETER,       // Invalid parameter passed
    TGCALLER_ERROR_NOT_INITIALIZED,         // TgCaller not initialized
    TGCALLER_ERROR_NOT_CONNECTED,           // Not connected to Telegram
    TGCALLER_ERROR_ALREADY_CONNECTED,       // Already connected
    TGCALLER_ERROR_CONNECTION_FAILED,       // Connection failed
    TGCALLER_ERROR_INVALID_CHAT,            // Invalid chat ID
    TGCALLER_ERROR_ALREADY_IN_CALL,         // Already in call
    TGCALLER_ERROR_NOT_IN_CALL,             // Not in call
    TGCALLER_ERROR_CALL_FAILED,             // Call operation failed
    TGCALLER_ERROR_STREAM_FAILED,           // Stream operation failed
    TGCALLER_ERROR_FILE_NOT_FOUND,          // Media file not found
    TGCALLER_ERROR_INVALID_FORMAT,          // Invalid media format
    TGCALLER_ERROR_CODEC_ERROR,             // Codec error
    TGCALLER_ERROR_DEVICE_ERROR,            // Audio/video device error
    TGCALLER_ERROR_PERMISSION_DENIED,       // Permission denied
    TGCALLER_ERROR_NETWORK_ERROR,           // Network error
    TGCALLER_ERROR_TIMEOUT,                 // Operation timeout
    TGCALLER_ERROR_OUT_OF_MEMORY,           // Out of memory
    TGCALLER_ERROR_UNKNOWN                  // Unknown error
} TgCallerError;

// Get error string
const char* tgcaller_error_string(TgCallerError error);
```

## Stream Status

### TgCallerStreamStatus

```c
typedef enum {
    TGCALLER_STREAM_IDLE,           // No active stream
    TGCALLER_STREAM_LOADING,        // Loading stream
    TGCALLER_STREAM_PLAYING,        // Stream is playing
    TGCALLER_STREAM_PAUSED,         // Stream is paused
    TGCALLER_STREAM_STOPPED,        // Stream is stopped
    TGCALLER_STREAM_ERROR           // Stream error
} TgCallerStreamStatus;

// Get stream status
TgCallerError tgcaller_get_stream_status(TgCaller* caller, int64_t chat_id, TgCallerStreamStatus* status);
```

## Call Status

### TgCallerCallStatus

```c
typedef enum {
    TGCALLER_CALL_IDLE,             // Not in call
    TGCALLER_CALL_CONNECTING,       // Connecting to call
    TGCALLER_CALL_CONNECTED,        // Connected to call
    TGCALLER_CALL_DISCONNECTING,    // Disconnecting from call
    TGCALLER_CALL_ERROR             // Call error
} TgCallerCallStatus;

// Get call status
TgCallerError tgcaller_get_call_status(TgCaller* caller, int64_t chat_id, TgCallerCallStatus* status);
```

## Codecs

### TgCallerCodec

```c
typedef enum {
    // Audio codecs
    TGCALLER_CODEC_OPUS,            // Opus codec (recommended for audio)
    TGCALLER_CODEC_AAC,             // AAC codec
    TGCALLER_CODEC_MP3,             // MP3 codec
    TGCALLER_CODEC_PCM,             // Raw PCM
    
    // Video codecs
    TGCALLER_CODEC_H264,            // H.264 codec (recommended for video)
    TGCALLER_CODEC_VP8,             // VP8 codec
    TGCALLER_CODEC_VP9,             // VP9 codec
    TGCALLER_CODEC_AV1              // AV1 codec
} TgCallerCodec;
```

## Media Formats

### TgCallerFormat

```c
typedef enum {
    TGCALLER_FORMAT_PCM,            // Raw PCM audio
    TGCALLER_FORMAT_MP3,            // MP3 audio
    TGCALLER_FORMAT_WAV,            // WAV audio
    TGCALLER_FORMAT_OGG,            // OGG audio
    TGCALLER_FORMAT_FLAC,           // FLAC audio
    TGCALLER_FORMAT_AAC,            // AAC audio
    TGCALLER_FORMAT_MP4,            // MP4 video
    TGCALLER_FORMAT_AVI,            // AVI video
    TGCALLER_FORMAT_MKV,            // MKV video
    TGCALLER_FORMAT_WEBM,           // WebM video
    TGCALLER_FORMAT_MOV             // MOV video
} TgCallerFormat;
```

## Quality Presets

### TgCallerQuality

```c
typedef enum {
    TGCALLER_QUALITY_LOW,           // Low quality (bandwidth optimized)
    TGCALLER_QUALITY_MEDIUM,        // Medium quality (balanced)
    TGCALLER_QUALITY_HIGH,          // High quality (quality optimized)
    TGCALLER_QUALITY_ULTRA,         // Ultra quality (maximum quality)
    TGCALLER_QUALITY_CUSTOM         // Custom quality (use specific config)
} TgCallerQuality;
```

## Repeat Modes

### TgCallerRepeatMode

```c
typedef enum {
    TGCALLER_REPEAT_NONE,           // No repeat
    TGCALLER_REPEAT_ONE,            // Repeat current track
    TGCALLER_REPEAT_ALL             // Repeat all tracks in queue
} TgCallerRepeatMode;

// Set repeat mode
TgCallerError tgcaller_set_repeat_mode(TgCaller* caller, int64_t chat_id, TgCallerRepeatMode mode);

// Get repeat mode
TgCallerError tgcaller_get_repeat_mode(TgCaller* caller, int64_t chat_id, TgCallerRepeatMode* mode);
```

## Event Types

### TgCallerStreamEventType

```c
typedef enum {
    TGCALLER_STREAM_STARTED,        // Stream started
    TGCALLER_STREAM_ENDED,          // Stream ended
    TGCALLER_STREAM_PAUSED,         // Stream paused
    TGCALLER_STREAM_RESUMED,        // Stream resumed
    TGCALLER_STREAM_POSITION,       // Position changed
    TGCALLER_STREAM_ERROR           // Stream error
} TgCallerStreamEventType;
```

### TgCallerCallEventType

```c
typedef enum {
    TGCALLER_CALL_JOINED,           // Joined call
    TGCALLER_CALL_LEFT,             // Left call
    TGCALLER_CALL_USER_JOINED,      // User joined call
    TGCALLER_CALL_USER_LEFT,        // User left call
    TGCALLER_CALL_KICKED,           // Kicked from call
    TGCALLER_CALL_ERROR             // Call error
} TgCallerCallEventType;
```

## Filter Types

### TgCallerFilterType

```c
typedef enum {
    // Audio filters
    TGCALLER_FILTER_ECHO,           // Echo effect
    TGCALLER_FILTER_REVERB,         // Reverb effect
    TGCALLER_FILTER_PITCH_SHIFT,    // Pitch shifting
    TGCALLER_FILTER_DISTORTION,     // Distortion effect
    TGCALLER_FILTER_NOISE_GATE,     // Noise gate
    TGCALLER_FILTER_COMPRESSOR,     // Audio compressor
    TGCALLER_FILTER_EQUALIZER,      // Equalizer
    
    // Video filters
    TGCALLER_FILTER_BLUR,           // Blur effect
    TGCALLER_FILTER_SHARPEN,        // Sharpen effect
    TGCALLER_FILTER_SEPIA,          // Sepia effect
    TGCALLER_FILTER_GRAYSCALE,      // Grayscale effect
    TGCALLER_FILTER_COLOR_ADJUST,   // Color adjustment
    TGCALLER_FILTER_COLOR_BALANCE,  // Color balance
    TGCALLER_FILTER_EDGE_DETECT,    // Edge detection
    TGCALLER_FILTER_CARTOON         // Cartoon effect
} TgCallerFilterType;
```

## Whisper Models

### TgCallerWhisperModel

```c
typedef enum {
    TGCALLER_WHISPER_TINY,          // Tiny model (~39 MB)
    TGCALLER_WHISPER_BASE,          // Base model (~74 MB)
    TGCALLER_WHISPER_SMALL,         // Small model (~244 MB)
    TGCALLER_WHISPER_MEDIUM,        // Medium model (~769 MB)
    TGCALLER_WHISPER_LARGE,         // Large model (~1550 MB)
    TGCALLER_WHISPER_LARGE_V2,      // Large v2 model (~1550 MB)
    TGCALLER_WHISPER_LARGE_V3       // Large v3 model (~1550 MB)
} TgCallerWhisperModel;
```

## Log Levels

### TgCallerLogLevel

```c
typedef enum {
    TGCALLER_LOG_TRACE,             // Trace level (most verbose)
    TGCALLER_LOG_DEBUG,             // Debug level
    TGCALLER_LOG_INFO,              // Info level
    TGCALLER_LOG_WARNING,           // Warning level
    TGCALLER_LOG_ERROR,             // Error level
    TGCALLER_LOG_CRITICAL,          // Critical level
    TGCALLER_LOG_OFF                // Logging disabled
} TgCallerLogLevel;

// Set log level
TgCallerError tgcaller_set_log_level(TgCallerLogLevel level);

// Get current log level
TgCallerLogLevel tgcaller_get_log_level(void);
```

## Device Types

### TgCallerDeviceType

```c
typedef enum {
    TGCALLER_DEVICE_AUDIO_INPUT,    // Audio input device (microphone)
    TGCALLER_DEVICE_AUDIO_OUTPUT,   // Audio output device (speakers)
    TGCALLER_DEVICE_VIDEO_INPUT,    // Video input device (camera)
    TGCALLER_DEVICE_MONITOR         // Monitor/display device
} TgCallerDeviceType;
```

## Connection Types

### TgCallerConnectionType

```c
typedef enum {
    TGCALLER_CONNECTION_UDP,        // UDP connection (default)
    TGCALLER_CONNECTION_TCP,        // TCP connection
    TGCALLER_CONNECTION_TLS         // TLS connection
} TgCallerConnectionType;

// Set connection type
TgCallerError tgcaller_set_connection_type(TgCaller* caller, TgCallerConnectionType type);
```

## Stream Types

### TgCallerStreamType

```c
typedef enum {
    TGCALLER_STREAM_AUDIO,          // Audio only stream
    TGCALLER_STREAM_VIDEO,          // Video stream (includes audio)
    TGCALLER_STREAM_SCREEN,         // Screen sharing stream
    TGCALLER_STREAM_MICROPHONE,     // Live microphone input
    TGCALLER_STREAM_CAMERA,         // Live camera input
    TGCALLER_STREAM_MIXED           // Mixed audio/video stream
} TgCallerStreamType;
```

## Usage Examples

### Error Handling

```c
TgCallerError error = tgcaller_join_call(caller, chat_id);

switch (error) {
    case TGCALLER_SUCCESS:
        printf("Successfully joined call\n");
        break;
    case TGCALLER_ERROR_NOT_CONNECTED:
        fprintf(stderr, "Not connected to Telegram\n");
        break;
    case TGCALLER_ERROR_INVALID_CHAT:
        fprintf(stderr, "Invalid chat ID\n");
        break;
    case TGCALLER_ERROR_ALREADY_IN_CALL:
        fprintf(stderr, "Already in call\n");
        break;
    default:
        fprintf(stderr, "Error: %s\n", tgcaller_error_string(error));
        break;
}
```

### Status Checking

```c
TgCallerStreamStatus status;
TgCallerError error = tgcaller_get_stream_status(caller, chat_id, &status);

if (error == TGCALLER_SUCCESS) {
    switch (status) {
        case TGCALLER_STREAM_PLAYING:
            printf("Stream is currently playing\n");
            break;
        case TGCALLER_STREAM_PAUSED:
            printf("Stream is paused\n");
            break;
        case TGCALLER_STREAM_IDLE:
            printf("No active stream\n");
            break;
        default:
            printf("Stream status: %d\n", status);
            break;
    }
}
```

### Quality Configuration

```c
// Use quality preset
TgCallerVideoConfig config = tgcaller_video_config_default();
config.quality = TGCALLER_QUALITY_HIGH;

// Or use specific codec
config.codec = TGCALLER_CODEC_H264;
config.quality = TGCALLER_QUALITY_CUSTOM;
config.bitrate = 2000000;  // 2 Mbps

TgCallerError error = tgcaller_set_video_config(caller, &config);
```

All enums provide meaningful values that can be used for configuration, status checking, and error handling throughout the TgCaller C API.