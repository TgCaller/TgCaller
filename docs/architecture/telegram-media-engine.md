# Telegram Media Engine: Implementation Contract

## Status

**Initial audio-only aiortc implementation added; Telegram interoperability is not yet verified.**

The branch now contains `AiortcTelegramMediaEngine` at `tgcaller/mtproto/engine/aiortc_engine.py`. It creates a local audio track, builds a join payload from a real aiortc local offer, translates Telegram's WebRTC transport response into a remote SDP answer, and waits for the ICE/DTLS connection state to become connected. It supports paced stereo 48 kHz signed 16-bit PCM input and explicitly rejects video publishing and Telegram stream/RTMP response modes.

This is a first implementation, not a claim of production readiness. CI unit tests can validate payload construction and SDP handling, but only a live Telegram group-call integration test can establish that Telegram accepts the negotiation and that audio is actually audible. The engine must fail closed when the response shape or transport is unsupported.

The implementation does not add PyTgCalls or NTgCalls as runtime dependencies. It uses aiortc as a low-level WebRTC transport and implements the Telegram signaling boundary itself. That alone does not guarantee wire compatibility.

## Official protocol facts

- Telegram's `phone.joinGroupCall` documentation says the local join payload includes a non-zero audio SSRC, ICE `ufrag` and `pwd`, and DTLS fingerprints; publishing video also requires `ssrc-groups`. See [Telegram's join method](https://core.telegram.org/method/phone.joinGroupCall).
- Telegram documents `UpdateGroupCallConnection.params` as the server response for the local group-call engine. A response with `{"stream": true}` or `{"stream": true, "rtmp": true}` indicates a different playback mode and must not be treated as a WebRTC answer. See [UpdateGroupCallConnection](https://core.telegram.org/constructor/updateGroupCallConnection).
- Telegram's group-call documentation requires checking whether the server still recognizes a joined SSRC and recreating a connection when it is missing. See [Group calls](https://core.telegram.org/api/group-calls).

These references describe Telegram's signaling contract. They do not replace a real media-transport interoperability test.

## Current supported boundary

- Main group-call audio connection using WebRTC mode.
- PCM input: 48 kHz, stereo, signed 16-bit little-endian frames up to 120 ms.
- Local join payload values are extracted from the actual aiortc local SDP, not placeholders.
- Remote ICE credentials, DTLS fingerprint/setup and ICE candidates are taken from Telegram's response.
- Stream and RTMP modes are rejected rather than falsely reporting an audio connection.
- Video publishing and screen sharing remain unsupported by this engine.

## Target architecture

Keep signaling and media transport separate:

- `telegram_backend.py`: resolve the active group call, issue Telegram raw RPCs, pass the join response to the engine, and compensate/clean up if negotiation fails.
- `media_engine.py`: stable interface and strict parsing/validation helpers.
- `engine/aiortc_engine.py`: current audio-only implementation, session lifecycle, PCM source, and Telegram-to-SDP negotiation adapter.
- Future modules may split session, signaling, audio sources, video, and error handling further as the implementation grows.

## Required session states

Each chat session must move only through:

`NEW -> PREPARING -> JOIN_REQUESTED -> NEGOTIATING -> CONNECTED -> CLOSING -> CLOSED`

Any failure before `CONNECTED` must release local sockets, ICE/DTLS objects, encoder state and tasks. If Telegram accepted the join request, rollback must issue a leave request using the SSRC accepted by that request. Cancellation must run the same cleanup path and then propagate `CancelledError`.

A session is healthy only when the underlying transport reports the negotiated connection is established; local state or a successful RPC alone is insufficient.

## Remaining acceptance gates

### Gate 1 — Protocol fixtures

- Add sanitized fixtures for real Telegram WebRTC response updates, including supported and unsupported response variants.
- Validate signed/unsigned SSRC representation, ICE candidates, DTLS setup/fingerprint, and codec negotiation against Telegram behavior.
- Never commit account credentials, access hashes, private call data or live secrets.

### Gate 2 — Transport interoperability

- Test a real join against a dedicated Telegram test group and confirm ICE/DTLS reaches connected.
- Confirm that Telegram accepts the local payload and remote SDP answer.
- Verify that remote RTP arrives and outbound RTP is accepted; a generic aiortc peer test is not sufficient.

### Gate 3 — Outbound audio

- Validate sample rate, channels, PCM frame duration, pacing and queue backpressure.
- Confirm actual audible output in a dedicated Telegram test group.
- Test end-of-stream, source replacement, cancellation and transport failure without silently dropping arbitrary bytes.

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
