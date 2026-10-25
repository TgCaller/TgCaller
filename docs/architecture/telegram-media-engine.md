# Telegram Media Engine: Implementation Contract

## Status

**Design / implementation gate — not a working media engine yet.**

TgCaller currently has a `TelegramMediaEngine` protocol and a Pyrogram MTProto signaling adapter. It does not yet have a concrete implementation that can establish Telegram-compatible media transport. The adapter must continue to fail closed until one exists. Passing unit tests for the adapter is not evidence that audio reaches a Telegram group call.

This plan deliberately does not add PyTgCalls or NTgCalls as runtime dependencies and does not treat a generic aiortc peer connection as Telegram-compatible by itself.

## Target boundary

Keep signaling and media transport separate:

- `telegram_backend.py`: resolve the active group call, issue Telegram raw RPCs, pass the join response to the engine, and compensate/clean up if negotiation fails.
- `media_engine.py`: stable interface only; no fake success or placeholder ICE/DTLS values.
- Proposed implementation package: `tgcaller/mtproto/engine/`
  - `session.py`: per-chat lifecycle and state.
  - `signaling.py`: convert Telegram call updates and connection parameters into the engine's internal representation.
  - `transport.py`: real ICE/DTLS/RTP transport implementation, with explicit capability checks.
  - `audio.py`: PCM input, Opus encoding/packetization, timing and outbound audio.
  - `sources.py`: stream/source lifecycle and cancellation.
  - `errors.py`: typed negotiation, transport and media errors.

The proposed names are a design target, not existing modules.

## Required session states

Each chat session must move only through:

`NEW -> PREPARING -> JOIN_REQUESTED -> NEGOTIATING -> CONNECTED -> CLOSING -> CLOSED`

Any failure before `CONNECTED` must release local sockets, ICE/DTLS objects, encoder state and tasks. If Telegram accepted the join request, rollback must issue a leave request using the SSRC accepted by that request. Cancellation must run the same cleanup path and then propagate `CancelledError`.

A session is healthy only when the underlying transport reports the negotiated connection is established; local state or a successful RPC alone is insufficient.

## Audio-first implementation gates

### Gate 1 — Protocol facts and test fixtures

- Capture/document the exact Telegram `phone.joinGroupCall` payload shape and the `updateGroupCallConnection` fields supported by the chosen Telegram layer.
- Build sanitized fixtures from protocol documentation or controlled test sessions; never commit account credentials, access hashes, private call data or live secrets.
- Validate audio SSRC, ICE credentials, DTLS fingerprint/setup, negotiated endpoints and returned server parameters.
- Reject missing or unknown required fields rather than manufacturing defaults.

### Gate 2 — Transport proof

- Implement or select a transport implementation that can be shown to match Telegram's group-call protocol without adding PyTgCalls/NTgCalls as a runtime dependency.
- Prove ICE connectivity, DTLS fingerprint verification, RTP/RTCP behavior, audio codec parameters and Telegram's connection-update handling in an isolated integration test.
- Do not mark this gate complete just because an aiortc offer/answer succeeds against a generic WebRTC peer.

### Gate 3 — Outbound audio

- Accept a documented PCM format and validate sample rate, channels and frame duration.
- Encode to the negotiated codec and send paced media frames with monotonic timestamps.
- Handle backpressure, end-of-stream, source replacement, cancellation and transport failure without silently dropping arbitrary bytes.
- Confirm actual audible output in a dedicated Telegram test group.

### Gate 4 — Lifecycle and reliability

- Test join success/failure, cancellation during every await boundary, duplicate join, stale session replacement, disconnect, source failure and process shutdown.
- Assert every acquired resource is released exactly once and no task remains running after close.
- Test reconnect separately from a fresh join; never reuse stale ICE/DTLS state.

### Gate 5 — Video and screen sharing

Only after audio-only transport is verified: negotiate video SSRC groups, codec/profile constraints, frame pacing, keyframes, source dimensions and screen-capture lifecycle. Video payload requirements must not be inferred from audio-only tests.

## Minimum acceptance criteria

- No fabricated join parameters or simulated connected state.
- No PyTgCalls/NTgCalls runtime dependency.
- Protocol-level tests cover valid and malformed server updates.
- Integration test demonstrates an actual Telegram group-call connection.
- Audio integration test demonstrates audible output in a real test group.
- Failed join and cancellation leave no local session or resource leak.
- CI tests and package build pass, and live verification is reported separately from CI.

## Current blocker

The repository does not yet contain a concrete implementation of the Telegram media protocol. Before writing transport code, the project must establish the exact signaling/media behavior it will implement and verify that the chosen low-level transport can reproduce it. Until then, `PyrogramGroupCallBackend` is only the signaling adapter and cannot stream media on its own.
