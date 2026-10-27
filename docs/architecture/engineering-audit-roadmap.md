# TgCaller Engineering Audit Roadmap

This is the tracked engineering plan for making TgCaller installable, internally consistent, and demonstrably functional. A passing unit-test suite or successful wheel build does **not** prove Telegram group-call interoperability. Live Telegram integration must be tested separately before any production-ready claim.

## Priority 0 — Installation and packaging

- [x] Remove platform-incompatible packages from mandatory dependencies when they are only needed by optional features (psutil moved to the optional monitoring extra).
- [x] Make CPU monitoring work when `psutil` is unavailable; expose a clear optional monitoring extra.
- [ ] Audit the full dependency graph on supported Python versions and platforms, including Android/Termux. Do not claim Termux support until a clean install is tested there.
- [ ] Ensure `pyproject.toml`, `requirements.txt`, extras, `setup.py`, and package metadata agree.
- [ ] Test clean install, `import tgcaller`, public exports, and wheel/sdist contents.

## Priority 1 — Telegram media-engine protocol

- [ ] Verify Telegram join-payload fields against real Telegram WebRTC group-call behavior.
- [ ] Verify `UpdateGroupCallConnection.params` parsing and distinguish WebRTC from stream/RTMP modes.
- [ ] Validate ICE candidate fields, DTLS fingerprint/setup roles, SDP direction, codec negotiation, SSRC sign/representation, and server-provided connection updates.
- [ ] Test join success, failed negotiation, timeout, cancellation, leave, reconnect, and resource cleanup.
- [ ] Run a real Telegram group-call integration test with logs showing ICE/DTLS connected and audible received playback. Unit tests alone are insufficient.

## Priority 2 — Audio playback and transport

- [ ] Verify FFmpeg source-to-PCM conversion for files, HTTP URLs, and HLS/m3u8.
- [ ] Verify PCM frame size, stereo/sample-rate assumptions, pacing, queue backpressure, and underrun behavior.
- [ ] Verify process stderr handling, non-zero exit reporting, cancellation, terminate/kill/reap, and repeated play/stop cycles.
- [ ] Verify transport errors are surfaced to callers and are never reported as successful playback.

## Priority 3 — YouTube pipeline

- [ ] Verify yt-dlp extraction for live, age/region-restricted, unavailable, and ordinary URLs.
- [ ] Verify stream start ordering, FFmpeg startup/EOF behavior, buffer producer/consumer lifecycle, callback delivery, and chunk ordering.
- [ ] Verify each audio chunk is actually sent through `caller.send_frame`; test disconnects and send failures.
- [ ] Test repeated start/stop and cancellation without orphaned processes or tasks.

## Priority 4 — Public API and lifecycle

- [ ] Audit `TgCaller(client=app)`, exports, type contracts, and optional dependency imports.
- [ ] Audit join/leave/play/stop/pause/resume/mute/volume/seek/recording return values for false-success behavior.
- [ ] Audit handler names, event ordering, duplicate registration, cancellation, and shutdown.
- [ ] Audit concurrent calls and per-chat session isolation.

## Priority 5 — Explicit feature gaps

- [ ] Implement and integration-test video negotiation/packetization before advertising video publishing.
- [ ] Implement and test microphone, camera, and screen-share capture paths against the Telegram media engine.
- [ ] Implement Spotify resolution/authentication legally and reliably; do not treat a Spotify URL as a directly playable media URL.
- [ ] Verify Whisper transcription, thumbnail generation, and media-device features independently.
- [ ] Keep unsupported features explicitly rejected rather than returning success.

## Priority 6 — Quality, docs, and release

- [ ] Add regression tests for each fixed defect.
- [ ] Run tests and distribution builds in CI; investigate any failing or missing checks.
- [ ] Make examples match the actually implemented API and supported features.
- [ ] Publish a new release only after compatibility, install, and integration checks pass; the public PyPI release is separate from this branch.

## Current inspection notes (2026-10-27)

- The repair branch contains an initial `AiortcTelegramMediaEngine` for audio-only WebRTC, including FFmpeg-to-PCM playback. Its own module documentation says real Telegram interoperability still needs a live integration test.
- The engine explicitly rejects video publishing and stream/RTMP modes; video, camera, and screen-share must not be described as implemented by this engine yet.
- Termux's `pip` build of psutil failed with “platform android is not supported”. The repair branch now removes psutil from mandatory package dependencies, makes CPU monitoring degrade safely when psutil is absent, and documents psutil as an optional `monitoring` extra.
- GitHub Actions run [40551027880](https://github.com/TgCaller/TgCaller/actions/runs/40551027880) passed the configured test suite and distribution build after the optional-psutil changes. This is CI-runner evidence only, not an Android installation test.
- YouTube code has an audio-only raw-PCM path and buffer callbacks that send chunks, but that path still needs targeted regression tests and live playback verification.
- A clean Termux install and live Telegram call are still unverified.
