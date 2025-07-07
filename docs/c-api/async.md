# Using Async

## Asynchronous Operations

TgCaller C API supports asynchronous operations for non-blocking execution.

## Async Callbacks

```c
#include "tgcaller.h"

// Async callback for stream operations
void stream_callback(TgCallerResult result, void* user_data) {
    if (result.success) {
        printf("Stream operation completed successfully\n");
    } else {
        printf("Stream operation failed: %s\n", result.error_message);
    }
}

// Start async stream
TgCallerError error = tgcaller_play_async(
    caller,
    chat_id,
    "audio.mp3",
    stream_callback,
    NULL  // user_data
);
```

## Event Loop Integration

```c
// Run event loop
while (tgcaller_is_running(caller)) {
    tgcaller_process_events(caller);
    usleep(1000);  // 1ms delay
}
```

## Thread Safety

```c
#include <pthread.h>

pthread_mutex_t tgcaller_mutex = PTHREAD_MUTEX_INITIALIZER;

void thread_safe_operation() {
    pthread_mutex_lock(&tgcaller_mutex);
    
    // TgCaller operations here
    tgcaller_join_call(caller, chat_id);
    
    pthread_mutex_unlock(&tgcaller_mutex);
}
```

## Async Examples

### Async File Playing

```c
typedef struct {
    char* filename;
    int chat_id;
} PlayContext;

void play_complete_callback(TgCallerResult result, void* user_data) {
    PlayContext* ctx = (PlayContext*)user_data;
    
    if (result.success) {
        printf("Finished playing: %s in chat %d\n", ctx->filename, ctx->chat_id);
    }
    
    free(ctx->filename);
    free(ctx);
}

void play_file_async(TgCaller* caller, int chat_id, const char* filename) {
    PlayContext* ctx = malloc(sizeof(PlayContext));
    ctx->filename = strdup(filename);
    ctx->chat_id = chat_id;
    
    tgcaller_play_async(caller, chat_id, filename, play_complete_callback, ctx);
}
```

### Async Queue Management

```c
typedef struct {
    char** queue;
    int count;
    int current;
} PlayQueue;

void queue_next_callback(TgCallerResult result, void* user_data) {
    PlayQueue* queue = (PlayQueue*)user_data;
    
    if (result.success && queue->current < queue->count - 1) {
        queue->current++;
        tgcaller_play_async(
            caller, 
            chat_id, 
            queue->queue[queue->current],
            queue_next_callback,
            queue
        );
    }
}
```