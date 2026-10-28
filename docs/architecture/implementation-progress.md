# TgCaller Implementation Progress

Last updated: 2026-10-28

Repository: https://github.com/TgCaller/TgCaller
Working branch: `fix/tgcaller-repository-repair`
Pull request: https://github.com/TgCaller/TgCaller/pull/4
Scope: Build TgCaller as its own Telegram group-call media engine/library. Do not claim live streaming works until verified against a real Telegram group call.

## Status legend

- [x] Completed in the repository and/or covered by automated tests.
- [~] Partially implemented; not yet proven end-to-end.
- [ ] Not done yet.

## Completed / automated-test coverage

- [x] Repair core exports, package version alignment, and public import tests.
- [x] Make connection operations fail closed instead of reporting simulated success.
- [x] Add Telegram MTProto backend boundaries, join payload validation, SSRC checks, and rollback/cleanup handling.
- [x] Add an initial `AiortcTelegramMediaEngine` for audio-only WebRTC negotiation, PCM input, and session cleanup.
- [x] Add parsing for `UpdateGroupCallConnection.params` and reject malformed/unsupported stream-mode responses.
- [x] Make the current YouTube pipeline explicitly audio-only; reject video requests until a video transport is implemented.
- [x] Fix YouTube chunk-generator startup ordering and await chunk delivery through the buffer callback.
- [x] Preserve PCM chunk order and avoid corrupting media with fake byte-truncation compression.
- [x] Add unit tests for media-engine payload/SDP helpers, backend validation, buffer callbacks, and YouTube pipeline behavior.
- [x] Fix async-iterable playback lifecycle: return after the first accepted frame, pump remaining frames in a managed task, and close/cancel the iterator when stopped.
- [x] Add regression tests for non-blocking async playback, empty sources, and clean cancellation.
- [x] Latest implementation CI passed: commit `d0cfe2a88748af6b04d6c0dcc46fd7df15898111`; Tests run #465: https://github.com/TgCaller/TgCaller/actions/runs/40632794605 (test suite and distribution build succeeded).

## In progress / not yet verified end-to-end

- [~] Validate the initial aiortc engine against real Telegram WebRTC negotiation. Unit tests do not prove Telegram accepts the generated join payload or that audio is audible.
- [~] Verify a real YouTube URL can be decoded by FFmpeg and its PCM is delivered through an actually connected Telegram call.
- [~] Confirm installed PyPI release compatibility separately from this repair branch; PyPI 1.0.3 does not automatically include branch changes.

## Next task (do one task at a time)

1. [ ] Review and harden the audio engine's negotiation/session lifecycle against the documented Telegram response contract. Add focused regression tests for any defects found, run CI, then update this checklist with the exact commit and result.

## Later tasks

2. [ ] Add sanitized protocol fixtures based on a real, authorized Telegram test call (never commit credentials or private call data).
3. [ ] Run a live integration test in a dedicated Telegram test group: join, negotiate ICE/DTLS, send audio, confirm audible playback, then leave cleanly.
4. [ ] Fix remaining YouTube/FFmpeg lifecycle and error-reporting issues revealed by integration tests.
5. [ ] Implement Telegram-compatible video publishing and packetization; until then, video, camera, and screen-sharing output must remain explicitly unsupported.
6. [ ] Add and verify source integrations (Spotify and m3u8) on top of the working media engine.
7. [ ] Add and verify Whisper transcription and thumbnail utilities.
8. [ ] Resolve Android/Termux installation compatibility (including `psutil`) and test the install instructions on-device.
9. [ ] After acceptance gates pass, review release metadata, update documentation, and publish a new package version intentionally.

## Rules for updating this list

- Update this file after each meaningful implementation task.
- Mark a task complete only when the code/test evidence supports it; keep live Telegram verification separate from CI.
- Record commit SHA and GitHub Actions URL for completed implementation tasks.
- Do not mark video, live streaming, or third-party source integrations as working based only on mocks/unit tests.
