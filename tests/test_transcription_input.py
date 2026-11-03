"""Tests for Whisper input normalization and worker cancellation."""

import asyncio
from unittest.mock import AsyncMock

import numpy as np
import pytest

from tgcaller.advanced.transcription import WhisperTranscription


def _bare_transcriber():
    transcriber = WhisperTranscription.__new__(WhisperTranscription)
    transcriber.is_transcribing = True
    transcriber.audio_buffer = []
    transcriber.buffer_duration = 5.0
    transcriber.sample_rate = 16000
    transcriber.logger = __import__("logging").getLogger(__name__)
    transcriber._task = None
    return transcriber


def test_add_audio_data_resamples_and_normalizes_integer_pcm():
    transcriber = _bare_transcriber()
    samples = np.full(8000, 16384, dtype=np.int16)

    transcriber.add_audio_data(samples, sample_rate=8000)

    assert len(transcriber.audio_buffer) == 16000
    assert transcriber.audio_buffer[0] == pytest.approx(0.5, abs=1e-3)


def test_add_audio_data_downmixes_stereo():
    transcriber = _bare_transcriber()
    samples = np.column_stack(
        [np.full(1600, 0.25, dtype=np.float32), np.full(1600, 0.75, dtype=np.float32)]
    )

    transcriber.add_audio_data(samples, sample_rate=16000)

    assert len(transcriber.audio_buffer) == 1600
    assert transcriber.audio_buffer[0] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_stop_transcription_cancels_and_awaits_worker():
    transcriber = _bare_transcriber()
    started = asyncio.Event()

    async def worker():
        started.set()
        await asyncio.Event().wait()

    transcriber._task = asyncio.create_task(worker())
    await started.wait()

    await transcriber.stop_transcription()

    assert transcriber._task is None
    assert transcriber.is_transcribing is False
    assert transcriber.audio_buffer == []
