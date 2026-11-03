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
