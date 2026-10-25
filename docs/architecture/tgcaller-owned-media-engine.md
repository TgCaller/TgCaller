# TgCaller-owned Telegram media engine: design plan

## Decision

TgCaller will implement and maintain its own Telegram group-call media engine. It will not depend on PyTgCalls or NTgCalls as its media runtime, and it will not present a third-party engine behind a renamed public API as if it were TgCaller's own implementation.

Using lower-level building blocks (for example, Python's aiortc, FFmpeg, codecs, and Pyrogram's MTProto API) is compatible with this decision: TgCaller must own the Telegram-specific negotiation, connection lifecycle, media routing, recovery, and public API. Each building block's role must be documented honestly.

## Current truth

The repository currently has the MTProto signaling adapter and a TelegramMediaEngine protocol, but it does not yet contain a complete working Telegram-compatible media engine. resolve_active_group_call only finds an existing call. Passing the current unit tests proves signaling orchestration and cleanup behavior, not successful live audio/video streaming.

Telegram requires a real engine-generated join payload containing a non-zero SSRC, ICE credentials, DTLS fingerprints, and video SSRC groups when video is published. The response to phone.joinGroupCall must then be applied to the local engine. Generic WebRTC support alone is not proof of compatibility.

Official references:
- https://core.telegram.org/method/phone.joinGroupCall
- https://core.telegram.org/api/group-calls
- https://core.telegram.org/method/phone.checkGroupCall

## Proposed internal layers

1. **Media session and resource ownership** — one isolated session per chat and per main/presentation connection; deterministic allocation and cleanup of SSRCs, peer connections, tasks, and tracks.
2. **Telegram parameter codec** — strictly parse and serialize the Telegram JSON contract; validate ICE credentials, fingerprints, SSRCs, candidates and video source groups. Never invent fallback values.
3. **WebRTC transport** — use low-level WebRTC primitives to create the actual connection, apply Telegram's returned parameters, drive ICE/DTLS state and expose real connection health. This layer is not complete until validated against Telegram's server behavior.
4. **Media pipeline** — decode inputs (file/URL/YouTube/HLS) to audio frames, normalize/resample, encode and feed the live sender. Add video capture/encoding only after audio transport works.
5. **Signaling and recovery** — the existing Pyrogram adapter owns MTProto RPCs; the media engine owns transport state. Rejoin only when Telegram no longer recognizes the SSRC, and preserve the original failure if rollback or cleanup also fails.
6. **Public API integration** — keep the caller-facing TgCaller(client=app) API stable and make unsupported capabilities fail clearly.
7. **Live acceptance tests** — a separately marked test using a real test group and two Telegram accounts must prove join/leave, audible audio, server-recognized SSRC, recovery and resource cleanup. Video and presentation require their own acceptance tests.

## Implementation order and acceptance gates

### Gate A — local WebRTC contract
- Implement parameter extraction/serialization helpers with unit tests and malformed-input cases.
- Confirm the generated parameters contain real values sourced from the active local transport, not placeholders.
- Confirm a failed or cancelled session releases all local resources.

### Gate B — Telegram audio join
- Implement the first real media engine class against TelegramMediaEngine.
- Consume the exact updateGroupCallConnection.params returned by Telegram.
- Do not report connected until the local transport reaches the required state.
- Prove a real audio track is audible in a live Telegram group call.

### Gate C — stream playback and recovery
- Connect FFmpeg-decoded audio frames to the sender.
- Add phone.checkGroupCall recovery and a fresh join when the server drops the source.
- Prove no leaked task, track or peer connection after repeated failures.

### Gate D — video and screen presentation
- Add video SSRC groups, frame encoding, and the separate presentation connection according to Telegram's API.
- Verify camera video and screen presentation in real calls independently.

## Non-negotiable rules

- No simulated success, placeholder credentials, fabricated SSRCs, or generic aiortc claims presented as proven Telegram compatibility.
- No PyTgCalls or NTgCalls runtime dependency.
- A test fake is allowed only in tests and must be clearly named as a fake.
- Keep protocol-specific behavior inside TgCaller modules with tests and documentation.
- Do not mark a gate complete based on unit tests alone; record live-call evidence separately.
