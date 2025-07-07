# Available Structs

## Core Structures

### TgCaller

```c
// Opaque structure for TgCaller instance
typedef struct TgCaller TgCaller;

// Create and destroy
TgCaller* tgcaller_create(void);
void tgcaller_destroy(TgCaller* caller);
```

### TgCallerAudioConfig

```c
typedef struct {
    int bitrate;                    // Audio bitrate in bps (8000-320000)
    int sample_rate;                // Sample rate in Hz (8000, 16000, 24000, 48000)
    int channels;                   // Number of channels (1=mono, 2=stereo)
    TgCallerCodec codec;            // Audio codec (OPUS, AAC)
    bool noise_suppression;         // Enable noise suppression
    bool echo_cancellation;         // Enable echo cancellation
    bool auto_gain_control;         // Enable automatic gain control
} TgCallerAudioConfig;

// Default configurations
TgCallerAudioConfig tgcaller_audio_config_default(void);
TgCallerAudioConfig tgcaller_audio_config_high_quality(void);
TgCallerAudioConfig tgcaller_audio_config_low_bandwidth(void);
```

### TgCallerVideoConfig

```c
typedef struct {
    int width;                      // Video width in pixels (320-1920)
    int height;                     // Video height in pixels (240-1080)
    int fps;                        // Frame rate (15, 24, 30, 60)
    int bitrate;                    // Video bitrate in bps (100000-5000000)
    TgCallerCodec codec;            // Video codec (H264, VP8)
    bool hardware_acceleration;     // Enable hardware acceleration
} TgCallerVideoConfig;

// Default configurations
TgCallerVideoConfig tgcaller_video_config_default(void);
TgCallerVideoConfig tgcaller_video_config_hd_720p(void);
TgCallerVideoConfig tgcaller_video_config_full_hd_1080p(void);
TgCallerVideoConfig tgcaller_video_config_low_quality(void);
```

## Stream Information

### TgCallerStreamInfo

```c
typedef struct {
    char* source;                   // Stream source (file path or URL)
    double duration;                // Total duration in seconds
    double position;                // Current position in seconds
    float volume;                   // Current volume (0.0 to 1.0)
    bool has_video;                 // Whether stream has video
    
    // Audio information
    int audio_sample_rate;          // Audio sample rate
    int audio_channels;             // Number of audio channels
    int audio_bitrate;              // Audio bitrate in bps
    
    // Video information (if has_video is true)
    int video_width;                // Video width
    int video_height;               // Video height
    int video_fps;                  // Video frame rate
    int video_bitrate;              // Video bitrate in bps
} TgCallerStreamInfo;

// Get stream information
TgCallerError tgcaller_get_stream_info(TgCaller* caller, int64_t chat_id, TgCallerStreamInfo* info);

// Free allocated strings in stream info
void tgcaller_stream_info_free(TgCallerStreamInfo* info);
```

### TgCallerMemoryStream

```c
typedef struct {
    const uint8_t* data;            // Pointer to audio data
    size_t size;                    // Size of data in bytes
    TgCallerFormat format;          // Audio format (PCM, etc.)
    int sample_rate;                // Sample rate in Hz
    int channels;                   // Number of channels
    int bits_per_sample;            // Bits per sample (8, 16, 24, 32)
} TgCallerMemoryStream;

// Play from memory
TgCallerError tgcaller_play_memory(TgCaller* caller, int64_t chat_id, const TgCallerMemoryStream* stream);
```

## Device Information

### TgCallerMonitorInfo

```c
typedef struct {
    int index;                      // Monitor index
    int x;                          // X position
    int y;                          // Y position
    int width;                      // Monitor width
    int height;                     // Monitor height
    bool is_primary;                // Whether this is the primary monitor
    char* name;                     // Monitor name
} TgCallerMonitorInfo;

// Get available monitors
TgCallerError tgcaller_get_monitors(TgCallerMonitorInfo** monitors, size_t* count);

// Free monitor info array
void tgcaller_monitors_free(TgCallerMonitorInfo* monitors, size_t count);
```

### TgCallerAudioDevice

```c
typedef struct {
    int index;                      // Device index
    char* name;                     // Device name
    int max_channels;               // Maximum number of channels
    double default_sample_rate;     // Default sample rate
    bool is_default;                // Whether this is the default device
} TgCallerAudioDevice;

// Get available audio devices
TgCallerError tgcaller_get_audio_devices(TgCallerAudioDevice** devices, size_t* count);

// Free audio device array
void tgcaller_audio_devices_free(TgCallerAudioDevice* devices, size_t count);
```

## Advanced Configurations

### TgCallerScreenConfig

```c
typedef struct {
    int monitor_index;              // Monitor to capture (-1 for all)
    int x;                          // Capture region X (0 for full monitor)
    int y;                          // Capture region Y (0 for full monitor)
    int width;                      // Capture width (0 for full monitor)
    int height;                     // Capture height (0 for full monitor)
    int fps;                        // Frame rate (15, 24, 30, 60)
    TgCallerQuality quality;        // Quality preset
} TgCallerScreenConfig;

// Default screen configuration
TgCallerScreenConfig tgcaller_screen_config_default(void);
```

### TgCallerMicConfig

```c
typedef struct {
    int device_index;               // Audio device index (-1 for default)
    int sample_rate;                // Sample rate in Hz
    int channels;                   // Number of channels
    bool noise_suppression;         // Enable noise suppression
    bool echo_cancellation;         // Enable echo cancellation
    bool auto_gain_control;         // Enable automatic gain control
    float gain;                     // Microphone gain (0.0 to 2.0)
} TgCallerMicConfig;

// Default microphone configuration
TgCallerMicConfig tgcaller_mic_config_default(void);
```

### TgCallerTranscriptionConfig

```c
typedef struct {
    TgCallerWhisperModel model;     // Whisper model to use
    char* language;                 // Language code (NULL for auto-detect)
    bool real_time;                 // Enable real-time transcription
    float confidence_threshold;     // Minimum confidence (0.0 to 1.0)
    bool translate;                 // Translate to English
} TgCallerTranscriptionConfig;

// Default transcription configuration
TgCallerTranscriptionConfig tgcaller_transcription_config_default(void);
```

## Filter Structures

### TgCallerAudioFilter

```c
typedef struct {
    TgCallerFilterType type;        // Filter type
    union {
        struct {
            float delay;            // Echo delay in seconds
            float decay;            // Echo decay factor
        } echo;
        
        struct {
            float room_size;        // Room size (0.0 to 1.0)
            float damping;          // Damping factor (0.0 to 1.0)
        } reverb;
        
        struct {
            float semitones;        // Pitch shift in semitones
        } pitch_shift;
        
        struct {
            float gain;             // Distortion gain
            float threshold;        // Distortion threshold
        } distortion;
        
        struct {
            float threshold;        // Gate threshold
            float ratio;            // Gate ratio
        } noise_gate;
    } parameters;
} TgCallerAudioFilter;
```

### TgCallerVideoFilter

```c
typedef struct {
    TgCallerFilterType type;        // Filter type
    union {
        struct {
            int kernel_size;        // Blur kernel size (odd number)
        } blur;
        
        struct {
            float brightness;       // Brightness adjustment (-1.0 to 1.0)
            float contrast;         // Contrast adjustment (-1.0 to 1.0)
            float saturation;       // Saturation adjustment (-1.0 to 1.0)
        } color_adjust;
        
        struct {
            float red_gain;         // Red channel gain
            float green_gain;       // Green channel gain
            float blue_gain;        // Blue channel gain
        } color_balance;
    } parameters;
} TgCallerVideoFilter;
```

## Event Structures

### TgCallerStreamEvent

```c
typedef struct {
    TgCallerStreamEventType type;   // Event type
    int64_t chat_id;                // Chat ID where event occurred
    char* source;                   // Stream source (for started events)
    char* error_message;            // Error message (for error events)
    double position;                // Current position (for position events)
    double duration;                // Total duration (for started events)
} TgCallerStreamEvent;

// Stream event callback
typedef void (*TgCallerStreamCallback)(TgCallerStreamEvent event, void* user_data);

// Set stream event callback
TgCallerError tgcaller_set_stream_callback(TgCaller* caller, TgCallerStreamCallback callback, void* user_data);
```

### TgCallerCallEvent

```c
typedef struct {
    TgCallerCallEventType type;     // Event type
    int64_t chat_id;                // Chat ID
    int64_t user_id;                // User ID (for user events)
    char* error_message;            // Error message (for error events)
} TgCallerCallEvent;

// Call event callback
typedef void (*TgCallerCallCallback)(TgCallerCallEvent event, void* user_data);

// Set call event callback
TgCallerError tgcaller_set_call_callback(TgCaller* caller, TgCallerCallCallback callback, void* user_data);
```

## YouTube Integration

### TgCallerYouTubeInfo

```c
typedef struct {
    char* title;                    // Video title
    char* uploader;                 // Uploader name
    int duration;                   // Duration in seconds
    int64_t view_count;             // View count
    char* description;              // Video description
    char* thumbnail_url;            // Thumbnail URL
} TgCallerYouTubeInfo;

// Get YouTube video information
TgCallerError tgcaller_get_youtube_info(const char* url, TgCallerYouTubeInfo* info);

// Free YouTube info
void tgcaller_youtube_info_free(TgCallerYouTubeInfo* info);
```

## Transcription Results

### TgCallerTranscriptionResult

```c
typedef struct {
    char* text;                     // Transcribed text
    char* language;                 // Detected language
    float confidence;               // Confidence score (0.0 to 1.0)
    double duration;                // Audio duration in seconds
    TgCallerTranscriptionSegment* segments;  // Detailed segments
    size_t segment_count;           // Number of segments
} TgCallerTranscriptionResult;

typedef struct {
    double start;                   // Segment start time
    double end;                     // Segment end time
    char* text;                     // Segment text
    float confidence;               // Segment confidence
} TgCallerTranscriptionSegment;

// Transcribe audio file
TgCallerError tgcaller_transcribe_file(const char* file_path, const char* language, TgCallerTranscriptionResult* result);

// Free transcription result
void tgcaller_transcription_result_free(TgCallerTranscriptionResult* result);
```

## Memory Management

All structures that contain allocated strings or arrays provide corresponding free functions:

```c
// Free functions for structures with allocated memory
void tgcaller_stream_info_free(TgCallerStreamInfo* info);
void tgcaller_monitors_free(TgCallerMonitorInfo* monitors, size_t count);
void tgcaller_audio_devices_free(TgCallerAudioDevice* devices, size_t count);
void tgcaller_youtube_info_free(TgCallerYouTubeInfo* info);
void tgcaller_transcription_result_free(TgCallerTranscriptionResult* result);
```

Always call the appropriate free function to avoid memory leaks when working with structures that contain allocated memory.