"""
Whisper Transcription - Real-time speech to text
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Callable, List, Dict, Any
import tempfile
import os

try:
    import whisper
    import torch
except ImportError:
    whisper = None
    torch = None

logger = logging.getLogger(__name__)


class WhisperTranscription:
    """Real-time speech transcription using OpenAI Whisper"""
    
    def __init__(
        self, 
        model_name: str = "base",
        language: Optional[str] = None,
        device: Optional[str] = None
    ):
        if whisper is None:
            raise ImportError("openai-whisper is required for transcription")
        
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
    
    async def load_model(self) -> bool:
        """Load Whisper model"""
        try:
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
        """Start real-time transcription"""
        if self.is_transcribing:
            self.logger.warning("Transcription already running")
            return True
        
        if self.model is None:
            success = await self.load_model()
            if not success:
                return False
        
        try:
            self.is_transcribing = True
            self.audio_buffer = []
            
            # Start transcription loop
            asyncio.create_task(self._transcription_loop())
            
            self.logger.info("Started real-time transcription")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start transcription: {e}")
            return False
    
    async def stop_transcription(self):
        """Stop transcription"""
        self.is_transcribing = False
        self.audio_buffer = []
        self.logger.info("Stopped transcription")
    
    def add_audio_data(self, audio_data: np.ndarray):
        """Add audio data for transcription"""
        if not self.is_transcribing:
            return
        
        try:
            # Convert to 16kHz mono if needed
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)  # Convert to mono
            
            # Resample to 16kHz if needed (simplified)
            # In production, use proper resampling
            
            self.audio_buffer.extend(audio_data.tolist())
            
            # Keep buffer size manageable
            max_buffer_size = int(self.buffer_duration * self.sample_rate)
            if len(self.audio_buffer) > max_buffer_size:
                self.audio_buffer = self.audio_buffer[-max_buffer_size:]
                
        except Exception as e:
            self.logger.error(f"Error adding audio data: {e}")
    
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