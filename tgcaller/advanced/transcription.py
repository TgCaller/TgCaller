"""
Whisper Transcription - Real-time speech to text
"""

from __future__ import annotations

import asyncio
import logging
import inspect
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING
import tempfile
import os

try:
    import whisper
    import torch
except ImportError:
    whisper = None
    torch = None

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


class WhisperTranscription:
    """Real-time speech transcription using OpenAI Whisper"""
    
    def __init__(
        self, 
        model_name: str = "base",
        language: Optional[str] = None,
        device: Optional[str] = None
    ):
        self.model_name = model_name
        self.language = language
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.is_transcribing = False
        self.audio_buffer = []
        self.buffer_duration = 5.0  # seconds
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.callbacks = []
        self.logger = logger
        self._task: Optional[asyncio.Task] = None
    
    async def load_model(self) -> bool:
        """Load Whisper model"""
        try:
            if whisper is None:
                raise ImportError("openai-whisper is required for transcription")
            self.logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Load model in thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(self.model_name, device=self.device)
            )
            
            self.logger.info("Whisper model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            return False
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add transcription callback"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove transcription callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start_transcription(self) -> bool:
        """Start a worker that waits for decoded audio supplied by the caller."""
        if self._task is not None and not self._task.done():
            return True
        if self.model is None and not await self.load_model():
            return False
        self.is_transcribing = True
        self.audio_buffer = []
        self._task = asyncio.create_task(self._transcription_loop())
        return True

    async def stop_transcription(self):
        """Stop and await the transcription worker."""
        self.is_transcribing = False
        task = self._task
        self._task = None
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.audio_buffer = []
        self.logger.info("Stopped transcription")

    def add_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """Append decoded audio, converting it to normalized 16 kHz mono PCM."""
        if not self.is_transcribing:
            return
        try:
            import numpy as np
            if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate <= 0:
                raise ValueError("sample_rate must be a positive integer")
            samples = np.asarray(audio_data)
            if samples.ndim == 2:
                samples = samples.mean(axis=1)
            elif samples.ndim != 1:
                raise ValueError("audio_data must be mono or samples-by-channels")
            if samples.size == 0:
                return
            if np.issubdtype(samples.dtype, np.integer):
                info = np.iinfo(samples.dtype)
                scale = float(max(abs(info.min), info.max))
                samples = samples.astype(np.float32) / scale
            else:
                samples = samples.astype(np.float32, copy=False)
            samples = np.nan_to_num(samples, copy=False)
            if sample_rate != self.sample_rate:
                output_length = max(1, round(samples.size * self.sample_rate / sample_rate))
                source_positions = np.arange(samples.size, dtype=np.float64)
                target_positions = np.linspace(0, samples.size - 1, output_length)
                samples = np.interp(target_positions, source_positions, samples).astype(np.float32)
            self.audio_buffer.extend(samples.tolist())
            max_buffer_size = int(self.buffer_duration * self.sample_rate)
            if len(self.audio_buffer) > max_buffer_size:
                self.audio_buffer = self.audio_buffer[-max_buffer_size:]
        except Exception as exc:
            self.logger.error("Error adding audio data: %s", exc)

    async def _transcription_loop(self):
        """Main transcription loop"""
        while self.is_transcribing:
            try:
                if len(self.audio_buffer) < self.sample_rate:  # At least 1 second
                    await asyncio.sleep(0.5)
                    continue
                
                # Get audio chunk
                audio_chunk = np.array(self.audio_buffer[-int(self.buffer_duration * self.sample_rate):])
                
                # Normalize audio
                if np.max(np.abs(audio_chunk)) > 0:
                    audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
                
                # Transcribe in thread
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self._transcribe_chunk,
                    audio_chunk
                )
                
                if result and result['text'].strip():
                    # Call callbacks
                    for callback in self.callbacks:
                        try:
                            callback(result)
                        except Exception as e:
                            self.logger.error(f"Error in transcription callback: {e}")
                
                await asyncio.sleep(1.0)  # Transcribe every second
                
            except Exception as e:
                self.logger.error(f"Error in transcription loop: {e}")
                await asyncio.sleep(1.0)
    
    def _transcribe_chunk(self, audio_chunk: np.ndarray) -> Optional[Dict[str, Any]]:
        """Transcribe audio chunk"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Save audio to temporary file
            import soundfile as sf
            sf.write(temp_path, audio_chunk, self.sample_rate)
            
            try:
                # Transcribe
                result = self.model.transcribe(
                    temp_path,
                    language=self.language,
                    fp16=False
                )
                
                return {
                    'text': result['text'],
                    'language': result['language'],
                    'segments': result.get('segments', []),
                    'confidence': self._calculate_confidence(result)
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            self.logger.error(f"Error transcribing chunk: {e}")
            return None
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate average confidence from segments"""
        try:
            segments = result.get('segments', [])
            if not segments:
                return 0.0
            
            total_confidence = sum(
                segment.get('avg_logprob', 0.0) for segment in segments
            )
            
            return max(0.0, min(1.0, (total_confidence / len(segments) + 1.0) / 2.0))
            
        except Exception:
            return 0.0
    
    async def transcribe_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio file"""
        try:
            if self.model is None:
                success = await self.load_model()
                if not success:
                    return None
            
            # Transcribe in thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(file_path, language=self.language)
            )
            
            return {
                'text': result['text'],
                'language': result['language'],
                'segments': result.get('segments', []),
                'duration': sum(seg.get('end', 0) - seg.get('start', 0) for seg in result.get('segments', []))
            }
            
        except Exception as e:
            self.logger.error(f"Error transcribing file: {e}")
            return None


class TranscriptionManager:
    """Manage transcription for multiple calls"""
    
    def __init__(self, caller):
        self.caller = caller
        self.transcribers: Dict[int, WhisperTranscription] = {}
        self.logger = logger
    
    async def start_transcription_for_call(
        self, 
        chat_id: int,
        model_name: str = "base",
        language: Optional[str] = None
    ) -> bool:
        """Start transcription for specific call"""
        try:
            if chat_id in self.transcribers:
                self.logger.warning(f"Transcription already active for chat {chat_id}")
                return True
            
            # Create transcriber
            transcriber = WhisperTranscription(model_name, language)
            transcriber.add_callback(
                lambda result: self._handle_transcription(chat_id, result)
            )
            
            # Start transcription
            success = await transcriber.start_transcription()
            if success:
                self.transcribers[chat_id] = transcriber
                self.logger.info(f"Started transcription for chat {chat_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start transcription for chat {chat_id}: {e}")
            return False
    
    async def stop_transcription_for_call(self, chat_id: int) -> bool:
        """Stop transcription for specific call"""
        try:
            if chat_id not in self.transcribers:
                return False
            
            transcriber = self.transcribers[chat_id]
            await transcriber.stop_transcription()
            
            del self.transcribers[chat_id]
            
            self.logger.info(f"Stopped transcription for chat {chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping transcription for chat {chat_id}: {e}")
            return False
    
    def add_audio_for_transcription(self, chat_id: int, audio_data: np.ndarray):
        """Add audio data for transcription"""
        if chat_id in self.transcribers:
            self.transcribers[chat_id].add_audio_data(audio_data)
    
    def _handle_transcription(self, chat_id: int, result: Dict[str, Any]):
        """Handle transcription result"""
        try:
            text = result['text'].strip()
            if text:
                self.logger.info(f"Transcription for chat {chat_id}: {text}")
                
                # You can send transcription to chat or handle it as needed
                # For example, send as message:
                # asyncio.create_task(
                #     self.caller.client.send_message(chat_id, f"🎤 {text}")
                # )
                
        except Exception as e:
            self.logger.error(f"Error handling transcription: {e}")
    
    async def cleanup(self):
        """Stop all transcriptions"""
        for chat_id in list(self.transcribers.keys()):
            await self.stop_transcription_for_call(chat_id)