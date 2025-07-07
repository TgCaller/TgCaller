# Basic Methods

## Core Functions

### Initialize TgCaller

```c
#include "tgcaller.h"

TgCaller* caller = tgcaller_create();
if (!caller) {
    fprintf(stderr, "Failed to create TgCaller instance\n");
    return -1;
}

// Set API credentials
TgCallerError error = tgcaller_set_credentials(caller, api_id, "api_hash");
if (error != TGCALLER_SUCCESS) {
    fprintf(stderr, "Failed to set credentials: %s\n", tgcaller_error_string(error));
    tgcaller_destroy(caller);
    return -1;
}
```

### Start TgCaller

```c
// Start the service
TgCallerError error = tgcaller_start(caller);
if (error != TGCALLER_SUCCESS) {
    fprintf(stderr, "Failed to start TgCaller: %s\n", tgcaller_error_string(error));
    return -1;
}

printf("TgCaller started successfully\n");
```

### Stop TgCaller

```c
// Stop the service
TgCallerError error = tgcaller_stop(caller);
if (error != TGCALLER_SUCCESS) {
    fprintf(stderr, "Failed to stop TgCaller: %s\n", tgcaller_error_string(error));
}

// Cleanup
tgcaller_destroy(caller);
```

## Call Management

### Join Call

```c
// Join a voice call
int64_t chat_id = -1001234567890;
TgCallerError error = tgcaller_join_call(caller, chat_id);

if (error == TGCALLER_SUCCESS) {
    printf("Successfully joined call in chat %lld\n", chat_id);
} else {
    fprintf(stderr, "Failed to join call: %s\n", tgcaller_error_string(error));
}
```

### Leave Call

```c
// Leave the call
TgCallerError error = tgcaller_leave_call(caller, chat_id);

if (error == TGCALLER_SUCCESS) {
    printf("Successfully left call in chat %lld\n", chat_id);
} else {
    fprintf(stderr, "Failed to leave call: %s\n", tgcaller_error_string(error));
}
```

### Check Connection Status

```c
// Check if connected to a specific call
bool is_connected = tgcaller_is_connected(caller, chat_id);
if (is_connected) {
    printf("Connected to call in chat %lld\n", chat_id);
} else {
    printf("Not connected to call in chat %lld\n", chat_id);
}

// Check if TgCaller service is running
bool is_running = tgcaller_is_running(caller);
if (is_running) {
    printf("TgCaller service is running\n");
} else {
    printf("TgCaller service is not running\n");
}
```

## Configuration

### Audio Configuration

```c
// Create audio configuration
TgCallerAudioConfig audio_config = {
    .bitrate = 128000,        // 128 kbps
    .sample_rate = 48000,     // 48 kHz
    .channels = 2,            // Stereo
    .codec = TGCALLER_CODEC_OPUS,
    .noise_suppression = true,
    .echo_cancellation = true
};

// Apply configuration
TgCallerError error = tgcaller_set_audio_config(caller, &audio_config);
if (error != TGCALLER_SUCCESS) {
    fprintf(stderr, "Failed to set audio config: %s\n", tgcaller_error_string(error));
}
```

### Video Configuration

```c
// Create video configuration
TgCallerVideoConfig video_config = {
    .width = 1280,
    .height = 720,
    .fps = 30,
    .bitrate = 1500000,       // 1.5 Mbps
    .codec = TGCALLER_CODEC_H264,
    .hardware_acceleration = true
};

// Apply configuration
TgCallerError error = tgcaller_set_video_config(caller, &video_config);
if (error != TGCALLER_SUCCESS) {
    fprintf(stderr, "Failed to set video config: %s\n", tgcaller_error_string(error));
}
```

## Error Handling

### Error Codes

```c
// Check specific error types
TgCallerError error = tgcaller_join_call(caller, chat_id);

switch (error) {
    case TGCALLER_SUCCESS:
        printf("Operation successful\n");
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
        fprintf(stderr, "Unknown error: %s\n", tgcaller_error_string(error));
        break;
}
```

### Error Messages

```c
// Get human-readable error message
const char* error_message = tgcaller_error_string(error);
printf("Error: %s\n", error_message);

// Get last error
TgCallerError last_error = tgcaller_get_last_error(caller);
if (last_error != TGCALLER_SUCCESS) {
    fprintf(stderr, "Last error: %s\n", tgcaller_error_string(last_error));
}
```

## Utility Functions

### Get Active Calls

```c
// Get list of active calls
int64_t* active_calls = NULL;
size_t count = 0;

TgCallerError error = tgcaller_get_active_calls(caller, &active_calls, &count);
if (error == TGCALLER_SUCCESS) {
    printf("Active calls (%zu):\n", count);
    for (size_t i = 0; i < count; i++) {
        printf("  Chat ID: %lld\n", active_calls[i]);
    }
    
    // Free the allocated memory
    free(active_calls);
} else {
    fprintf(stderr, "Failed to get active calls: %s\n", tgcaller_error_string(error));
}
```

### Get Version

```c
// Get TgCaller version
const char* version = tgcaller_get_version();
printf("TgCaller version: %s\n", version);

// Get build information
const char* build_info = tgcaller_get_build_info();
printf("Build info: %s\n", build_info);
```

## Complete Example

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "tgcaller.h"

int main() {
    // Create TgCaller instance
    TgCaller* caller = tgcaller_create();
    if (!caller) {
        fprintf(stderr, "Failed to create TgCaller\n");
        return -1;
    }
    
    // Set credentials
    int api_id = 12345;
    const char* api_hash = "your_api_hash";
    
    TgCallerError error = tgcaller_set_credentials(caller, api_id, api_hash);
    if (error != TGCALLER_SUCCESS) {
        fprintf(stderr, "Failed to set credentials\n");
        tgcaller_destroy(caller);
        return -1;
    }
    
    // Start TgCaller
    error = tgcaller_start(caller);
    if (error != TGCALLER_SUCCESS) {
        fprintf(stderr, "Failed to start TgCaller\n");
        tgcaller_destroy(caller);
        return -1;
    }
    
    // Join call
    int64_t chat_id = -1001234567890;
    error = tgcaller_join_call(caller, chat_id);
    if (error == TGCALLER_SUCCESS) {
        printf("Joined call successfully\n");
        
        // Wait for 10 seconds
        sleep(10);
        
        // Leave call
        tgcaller_leave_call(caller, chat_id);
        printf("Left call\n");
    }
    
    // Stop and cleanup
    tgcaller_stop(caller);
    tgcaller_destroy(caller);
    
    return 0;
}
```