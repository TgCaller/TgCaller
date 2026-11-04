# Incoming Audio

This page documents the incoming audio callback, its queueing behavior, and the current verification boundary.


## Incoming Audio Frames

The audio-only media engine can deliver decoded audio received from remote
participants through the `on_audio_frame` event.

Register an application handler with the decorator:

```python
@caller.on_audio_frame
async def on_audio_frame(client, chat_id, frame):
    # frame is an aiortc/av AudioFrame containing decoded remote audio.
    print(
        f"Audio received in {chat_id}: "
        f"{frame.samples} samples at {frame.sample_rate} Hz"
    )
```

The callback arguments are:

- `client`: the Pyrogram client passed to `TgCaller`.
- `chat_id`: the Telegram group-call chat ID.
- `frame`: a decoded `av.AudioFrame` supplied by aiortc.

The callback is invoked for remote audio tracks received by the joined call.
It is not a microphone-capture callback and does not report the audio that
your own client is publishing.

### Dispatch and backpressure

Incoming tracks are drained into a bounded per-call queue before application
callbacks run. The default queue capacity is 50 frames. If the queue is full,
the oldest queued frame is discarded so newer real-time audio can be delivered.
This favors low latency over preserving every frame during a slow consumer.

Async callbacks have a default execution timeout of 0.25 seconds. Callback
exceptions and async callback timeouts are logged and do not terminate the
remote track receive loop. Keep handlers short; for expensive processing,
enqueue work into an application-managed worker. Prefer `async def` handlers:
a synchronous handler executes on the event loop and cannot be interrupted by
the async callback timeout.

### Scope and verification

This API describes the implemented local aiortc receive/dispatch path.
A passing local RTP test does not establish Telegram live-call interoperability.
That still requires a live Telegram group call with valid API credentials and
an active call. The current media engine is audio-only; video receive/publish
is not documented as supported by this path.


## Reading receive counters

Applications can inspect a defensive snapshot through the public client:

```python
stats = caller.get_audio_receive_stats(chat_id)

print("received:", stats.get("frames_received", 0))
print("delivered:", stats.get("frames_delivered", 0))
print("dropped:", stats.get("frames_dropped", 0))
print("callback errors:", stats.get("callback_errors", 0))
print("callback timeouts:", stats.get("callback_timeouts", 0))
```

The returned mapping contains local engine counters:

| Counter | Meaning |
| --- | --- |
| `frames_received` | Decoded frames read from remote WebRTC audio tracks |
| `frames_delivered` | Frames whose application callback completed successfully |
| `frames_dropped` | Frames discarded from the bounded queue to favor fresh audio |
| `callback_errors` | Application callback invocations that raised an exception |
| `callback_timeouts` | Async application callback invocations that exceeded the timeout |

The method returns a snapshot, so changing the returned dictionary does not
change the engine's counters. A missing session returns zero-valued counters
from the built-in engine. A custom transport that does not implement this
optional capability returns an empty mapping.
