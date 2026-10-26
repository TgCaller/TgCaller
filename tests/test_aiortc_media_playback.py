import asyncio
from types import SimpleNamespace

import pytest

from tgcaller.exceptions import ConnectionError
from tgcaller.mtproto.engine.aiortc_engine import AiortcTelegramMediaEngine
from tgcaller.types import MediaStream


class FakeStdout:
    def __init__(self, data):
        self.data = data

    async def read(self, size):
        if not self.data:
            return b""
        chunk = self.data[:size]
        self.data = self.data[size:]
        return chunk


class FakeProcess:
    def __init__(self, data, return_code=0):
        self.stdout = FakeStdout(data)
        self.returncode = None
        self.final_return_code = return_code
        self.terminated = False
        self.killed = False

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    async def wait(self):
        if self.returncode is None:
            self.returncode = -15 if self.terminated else self.final_return_code
        return self.returncode


class FakeTrack:
    def __init__(self):
        self.frames = []

    async def push(self, data):
        self.frames.append(data)

    def clear(self):
        self.frames.clear()

    def stop(self):
        pass


def connected_engine():
    engine = AiortcTelegramMediaEngine(connect_timeout=1)
    track = FakeTrack()
    engine._sessions[-100123] = SimpleNamespace(
        pc=SimpleNamespace(connectionState="connected"),
        track=track,
    )
    return engine, track


@pytest.mark.asyncio
async def test_media_stream_source_is_decoded_and_pushed_as_pcm(monkeypatch):
    engine, track = connected_engine()
    output = b"a" * 3840 + b"b" * 3840 + b"c" * 4
    process = FakeProcess(output)
    captured = {}

    async def fake_create_subprocess_exec(*command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    started = await engine.play_stream(
        -100123,
        MediaStream(source="https://media.example/song.mp3", duration=3),
    )
    task = engine._stream_tasks[-100123]
    await task

    assert started is True
    assert track.frames == [b"a" * 3840, b"b" * 3840, b"c" * 4]
    command = captured["command"]
    assert "-i" in command
    assert "https://media.example/song.mp3" in command
    assert "-vn" in command
    assert "pcm_s16le" in command
    assert command[-2:] == ("s16le", "pipe:1")
    assert captured["kwargs"]["stdout"] == asyncio.subprocess.PIPE
    assert captured["kwargs"]["stderr"] == asyncio.subprocess.DEVNULL
    assert process.returncode == 0


@pytest.mark.asyncio
async def test_media_stream_source_fails_if_ffmpeg_produces_no_audio(monkeypatch):
    engine, _ = connected_engine()
    process = FakeProcess(b"", return_code=1)

    async def fake_create_subprocess_exec(*_command, **_kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    with pytest.raises(ConnectionError, match="produced no audio output"):
        await engine.play_stream(-100123, MediaStream(source="missing.mp3"))

    assert -100123 not in engine._stream_processes
    assert -100123 not in engine._stream_tasks


@pytest.mark.asyncio
async def test_stop_stream_cancels_source_task_and_reaps_ffmpeg(monkeypatch):
    engine, _ = connected_engine()
    gate = asyncio.Event()

    class BlockingStdout:
        def __init__(self):
            self.first = True

        async def read(self, size):
            if self.first:
                self.first = False
                return b"x" * size
            await gate.wait()
            return b""

    class BlockingProcess(FakeProcess):
        def __init__(self):
            super().__init__(b"")
            self.stdout = BlockingStdout()

    process = BlockingProcess()

    async def fake_create_subprocess_exec(*_command, **_kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    assert await engine.play_stream(-100123, MediaStream(source="song.mp3"))
    await asyncio.sleep(0)
    assert await engine.stop_stream(-100123)
    assert process.terminated is True
    assert process.returncode is not None
    assert -100123 not in engine._stream_tasks
