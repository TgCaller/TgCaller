# Advanced Methods

## Screen Sharing

### Start Screen Sharing

```c
#include "tgcaller.h"

// Screen sharing configuration
TgCallerScreenConfig screen_config = {
    .monitor_index = 0,        // Primary monitor
    .x = 0,                    // Capture from x=0
    .y = 0,                    // Capture from y=0
    .width = 1920,             // Capture width
    .height = 1080,            // Capture height
    .fps = 30,                 // 30 FPS
    .quality = TGCALLER_QUALITY_HIGH
};

// Start screen sharing
TgCallerError error = tgcaller_start_screen_share(caller, chat_id, &screen_config);
if (error == TGCALLER_SUCCESS) {
    printf("Screen sharing started\n");
} else {
    fprintf(stderr, "Failed to start screen sharing: %s\n", tgcaller_error_string(error));
}
```

### Stop Screen Sharing

```c
// Stop screen sharing
TgCallerError error = tgcaller_stop_screen_share(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Screen sharing stopped\n");
}
```

### List Available Monitors

```c
// Get available monitors
TgCallerMonitorInfo* monitors = NULL;
size_t monitor_count = 0;

TgCallerError error = tgcaller_get_monitors(&monitors, &monitor_count);
if (error == TGCALLER_SUCCESS) {
    printf("Available monitors (%zu):\n", monitor_count);
    
    for (size_t i = 0; i < monitor_count; i++) {
        printf("  Monitor %zu: %dx%d at (%d, %d)\n",
               i,
               monitors[i].width,
               monitors[i].height,
               monitors[i].x,
               monitors[i].y);
    }
    
    // Free the allocated memory
    free(monitors);
} else {
    fprintf(stderr, "Failed to get monitors: %s\n", tgcaller_error_string(error));
}
```

## Microphone Streaming

### Start Microphone Stream

```c
// Microphone configuration
TgCallerMicConfig mic_config = {
    .device_index = -1,        // Default device
    .sample_rate = 48000,      // 48 kHz
    .channels = 1,             // Mono
    .noise_suppression = true,
    .echo_cancellation = true,
    .auto_gain_control = true
};

// Start microphone streaming
TgCallerError error = tgcaller_start_microphone(caller, chat_id, &mic_config);
if (error == TGCALLER_SUCCESS) {
    printf("Microphone streaming started\n");
} else {
    fprintf(stderr, "Failed to start microphone: %s\n", tgcaller_error_string(error));
}
```

### Stop Microphone Stream

```c
// Stop microphone streaming
TgCallerError error = tgcaller_stop_microphone(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Microphone streaming stopped\n");
}
```

### List Audio Devices

```c
// Get available audio input devices
TgCallerAudioDevice* devices = NULL;
size_t device_count = 0;

TgCallerError error = tgcaller_get_audio_devices(&devices, &device_count);
if (error == TGCALLER_SUCCESS) {
    printf("Available audio devices (%zu):\n", device_count);
    
    for (size_t i = 0; i < device_count; i++) {
        printf("  Device %d: %s (%d channels, %.0f Hz)\n",
               devices[i].index,
               devices[i].name,
               devices[i].max_channels,
               devices[i].default_sample_rate);
    }
    
    // Free the allocated memory
    free(devices);
} else {
    fprintf(stderr, "Failed to get audio devices: %s\n", tgcaller_error_string(error));
}
```

## YouTube Integration

### Play YouTube Video

```c
// Play YouTube video directly
const char* youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";

TgCallerError error = tgcaller_play_youtube(caller, chat_id, youtube_url);
if (error == TGCALLER_SUCCESS) {
    printf("Started playing YouTube video\n");
} else {
    fprintf(stderr, "Failed to play YouTube video: %s\n", tgcaller_error_string(error));
}
```

### Search and Play YouTube

```c
// Search YouTube and play first result
const char* search_query = "relaxing music";

TgCallerError error = tgcaller_search_and_play_youtube(caller, chat_id, search_query);
if (error == TGCALLER_SUCCESS) {
    printf("Started playing YouTube search result\n");
} else {
    fprintf(stderr, "Failed to search and play: %s\n", tgcaller_error_string(error));
}
```

### Get YouTube Video Info

```c
// Get video information
TgCallerYouTubeInfo video_info;
const char* youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";

TgCallerError error = tgcaller_get_youtube_info(youtube_url, &video_info);
if (error == TGCALLER_SUCCESS) {
    printf("Video Info:\n");
    printf("  Title: %s\n", video_info.title);
    printf("  Duration: %d seconds\n", video_info.duration);
    printf("  Uploader: %s\n", video_info.uploader);
    printf("  Views: %lld\n", video_info.view_count);
    
    // Free allocated strings
    free(video_info.title);
    free(video_info.uploader);
} else {
    fprintf(stderr, "Failed to get video info: %s\n", tgcaller_error_string(error));
}
```

## Speech Transcription

### Start Transcription

```c
// Transcription configuration
TgCallerTranscriptionConfig transcription_config = {
    .model = TGCALLER_WHISPER_BASE,    // Whisper model
    .language = "en",                   // Language (NULL for auto-detect)
    .real_time = true,                  // Real-time transcription
    .confidence_threshold = 0.5f        // Minimum confidence
};

// Transcription callback
void transcription_callback(const char* text, float confidence, void* user_data) {
    printf("Transcription (%.1f%%): %s\n", confidence * 100, text);
}

// Start transcription
TgCallerError error = tgcaller_start_transcription(
    caller, 
    chat_id, 
    &transcription_config,
    transcription_callback,
    NULL  // user_data
);

if (error == TGCALLER_SUCCESS) {
    printf("Transcription started\n");
} else {
    fprintf(stderr, "Failed to start transcription: %s\n", tgcaller_error_string(error));
}
```

### Stop Transcription

```c
// Stop transcription
TgCallerError error = tgcaller_stop_transcription(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Transcription stopped\n");
}
```

### Transcribe Audio File

```c
// Transcribe audio file
TgCallerTranscriptionResult result;
const char* audio_file = "speech.wav";

TgCallerError error = tgcaller_transcribe_file(audio_file, "en", &result);
if (error == TGCALLER_SUCCESS) {
    printf("Transcription Result:\n");
    printf("  Text: %s\n", result.text);
    printf("  Language: %s\n", result.language);
    printf("  Confidence: %.1f%%\n", result.confidence * 100);
    printf("  Duration: %.1f seconds\n", result.duration);
    
    // Free allocated strings
    free(result.text);
    free(result.language);
} else {
    fprintf(stderr, "Failed to transcribe file: %s\n", tgcaller_error_string(error));
}
```

## Audio/Video Filters

### Apply Audio Filters

```c
// Audio filter configuration
TgCallerAudioFilter audio_filter = {
    .type = TGCALLER_FILTER_ECHO,
    .parameters = {
        .echo = {
            .delay = 0.3f,      // 300ms delay
            .decay = 0.5f       // 50% decay
        }
    }
};

// Apply audio filter
TgCallerError error = tgcaller_add_audio_filter(caller, chat_id, &audio_filter);
if (error == TGCALLER_SUCCESS) {
    printf("Audio filter applied\n");
} else {
    fprintf(stderr, "Failed to apply audio filter: %s\n", tgcaller_error_string(error));
}
```

### Apply Video Filters

```c
// Video filter configuration
TgCallerVideoFilter video_filter = {
    .type = TGCALLER_FILTER_BLUR,
    .parameters = {
        .blur = {
            .kernel_size = 15   // Blur intensity
        }
    }
};

// Apply video filter
TgCallerError error = tgcaller_add_video_filter(caller, chat_id, &video_filter);
if (error == TGCALLER_SUCCESS) {
    printf("Video filter applied\n");
} else {
    fprintf(stderr, "Failed to apply video filter: %s\n", tgcaller_error_string(error));
}
```

### Remove Filters

```c
// Remove all audio filters
TgCallerError error = tgcaller_clear_audio_filters(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Audio filters cleared\n");
}

// Remove all video filters
error = tgcaller_clear_video_filters(caller, chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Video filters cleared\n");
}
```

## Bridged Calls

### Create Bridge

```c
// Create bridge between multiple chats
int64_t chat_ids[] = {-1001234567890, -1009876543210, -1001122334455};
size_t chat_count = 3;

TgCallerError error = tgcaller_create_bridge(caller, "conference", chat_ids, chat_count);
if (error == TGCALLER_SUCCESS) {
    printf("Bridge created successfully\n");
} else {
    fprintf(stderr, "Failed to create bridge: %s\n", tgcaller_error_string(error));
}
```

### Destroy Bridge

```c
// Destroy bridge
TgCallerError error = tgcaller_destroy_bridge(caller, "conference");
if (error == TGCALLER_SUCCESS) {
    printf("Bridge destroyed\n");
}
```

### Add Chat to Bridge

```c
// Add chat to existing bridge
int64_t new_chat_id = -1005566778899;

TgCallerError error = tgcaller_bridge_add_chat(caller, "conference", new_chat_id);
if (error == TGCALLER_SUCCESS) {
    printf("Chat added to bridge\n");
}
```

## Plugin System

### Load Plugin

```c
// Load plugin from shared library
const char* plugin_path = "./plugins/echo_plugin.so";

TgCallerError error = tgcaller_load_plugin(caller, plugin_path);
if (error == TGCALLER_SUCCESS) {
    printf("Plugin loaded successfully\n");
} else {
    fprintf(stderr, "Failed to load plugin: %s\n", tgcaller_error_string(error));
}
```

### Unload Plugin

```c
// Unload plugin
TgCallerError error = tgcaller_unload_plugin(caller, "echo_plugin");
if (error == TGCALLER_SUCCESS) {
    printf("Plugin unloaded\n");
}
```

### List Loaded Plugins

```c
// Get list of loaded plugins
char** plugin_names = NULL;
size_t plugin_count = 0;

TgCallerError error = tgcaller_get_loaded_plugins(caller, &plugin_names, &plugin_count);
if (error == TGCALLER_SUCCESS) {
    printf("Loaded plugins (%zu):\n", plugin_count);
    
    for (size_t i = 0; i < plugin_count; i++) {
        printf("  %s\n", plugin_names[i]);
        free(plugin_names[i]);  // Free individual strings
    }
    
    free(plugin_names);  // Free array
} else {
    fprintf(stderr, "Failed to get loaded plugins: %s\n", tgcaller_error_string(error));
}
```

## Complete Advanced Example

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "tgcaller.h"

void transcription_callback(const char* text, float confidence, void* user_data) {
    printf("🎤 Transcription (%.1f%%): %s\n", confidence * 100, text);
}

int main() {
    TgCaller* caller = tgcaller_create();
    if (!caller) return -1;
    
    // Setup and start
    tgcaller_set_credentials(caller, 12345, "api_hash");
    tgcaller_start(caller);
    
    int64_t chat_id = -1001234567890;
    
    // Join call
    tgcaller_join_call(caller, chat_id);
    
    // Start screen sharing
    TgCallerScreenConfig screen_config = {
        .monitor_index = 0,
        .fps = 30,
        .quality = TGCALLER_QUALITY_HIGH
    };
    tgcaller_start_screen_share(caller, chat_id, &screen_config);
    
    // Start transcription
    TgCallerTranscriptionConfig transcription_config = {
        .model = TGCALLER_WHISPER_BASE,
        .language = "en",
        .real_time = true,
        .confidence_threshold = 0.7f
    };
    tgcaller_start_transcription(caller, chat_id, &transcription_config, transcription_callback, NULL);
    
    // Apply audio filter
    TgCallerAudioFilter echo_filter = {
        .type = TGCALLER_FILTER_ECHO,
        .parameters.echo = { .delay = 0.3f, .decay = 0.4f }
    };
    tgcaller_add_audio_filter(caller, chat_id, &echo_filter);
    
    // Run for 60 seconds
    sleep(60);
    
    // Cleanup
    tgcaller_stop_screen_share(caller, chat_id);
    tgcaller_stop_transcription(caller, chat_id);
    tgcaller_clear_audio_filters(caller, chat_id);
    tgcaller_leave_call(caller, chat_id);
    tgcaller_stop(caller);
    tgcaller_destroy(caller);
    
    return 0;
}
```