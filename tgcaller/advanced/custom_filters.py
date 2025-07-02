"""
Custom Audio and Video Filters
"""

import numpy as np
import logging
from typing import Optional, Dict, Any
try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)


class AudioFilters:
    """Advanced audio processing filters"""
    
    def __init__(self):
        self.logger = logger
        self.filters = {}
    
    def apply_echo(
        self, 
        audio_data: np.ndarray, 
        delay: float = 0.3, 
        decay: float = 0.3
    ) -> np.ndarray:
        """Apply echo effect"""
        try:
            sample_rate = 48000  # Default sample rate
            delay_samples = int(delay * sample_rate)
            
            if len(audio_data) <= delay_samples:
                return audio_data
            
            # Create echo
            echo_data = np.zeros_like(audio_data)
            echo_data[delay_samples:] = audio_data[:-delay_samples] * decay
            
            # Mix original with echo
            return audio_data + echo_data
            
        except Exception as e:
            self.logger.error(f"Error applying echo: {e}")
            return audio_data
    
    def apply_reverb(
        self, 
        audio_data: np.ndarray, 
        room_size: float = 0.5,
        damping: float = 0.5
    ) -> np.ndarray:
        """Apply reverb effect"""
        try:
            # Simple reverb implementation
            reverb_data = np.copy(audio_data)
            
            # Apply multiple delayed echoes with decreasing amplitude
            delays = [0.03, 0.05, 0.07, 0.09, 0.11]  # seconds
            sample_rate = 48000
            
            for i, delay in enumerate(delays):
                delay_samples = int(delay * sample_rate)
                if len(audio_data) > delay_samples:
                    amplitude = (1.0 - damping) * (0.8 ** i) * room_size
                    reverb_data[delay_samples:] += audio_data[:-delay_samples] * amplitude
            
            return reverb_data
            
        except Exception as e:
            self.logger.error(f"Error applying reverb: {e}")
            return audio_data
    
    def apply_pitch_shift(
        self, 
        audio_data: np.ndarray, 
        semitones: float
    ) -> np.ndarray:
        """Apply pitch shifting"""
        try:
            # Simple pitch shift using resampling
            shift_factor = 2 ** (semitones / 12.0)
            
            # Resample audio
            new_length = int(len(audio_data) / shift_factor)
            indices = np.linspace(0, len(audio_data) - 1, new_length)
            
            # Interpolate
            shifted_audio = np.interp(indices, np.arange(len(audio_data)), audio_data)
            
            # Pad or truncate to original length
            if len(shifted_audio) < len(audio_data):
                padded = np.zeros_like(audio_data)
                padded[:len(shifted_audio)] = shifted_audio
                return padded
            else:
                return shifted_audio[:len(audio_data)]
                
        except Exception as e:
            self.logger.error(f"Error applying pitch shift: {e}")
            return audio_data
    
    def apply_distortion(
        self, 
        audio_data: np.ndarray, 
        gain: float = 2.0,
        threshold: float = 0.7
    ) -> np.ndarray:
        """Apply distortion effect"""
        try:
            # Apply gain
            distorted = audio_data * gain
            
            # Clip at threshold
            distorted = np.clip(distorted, -threshold, threshold)
            
            # Normalize
            if np.max(np.abs(distorted)) > 0:
                distorted = distorted / np.max(np.abs(distorted))
            
            return distorted
            
        except Exception as e:
            self.logger.error(f"Error applying distortion: {e}")
            return audio_data
    
    def apply_noise_gate(
        self, 
        audio_data: np.ndarray, 
        threshold: float = 0.01,
        ratio: float = 10.0
    ) -> np.ndarray:
        """Apply noise gate"""
        try:
            # Calculate amplitude
            amplitude = np.abs(audio_data)
            
            # Apply gate
            gate_mask = amplitude > threshold
            gated_audio = np.where(
                gate_mask, 
                audio_data, 
                audio_data / ratio
            )
            
            return gated_audio
            
        except Exception as e:
            self.logger.error(f"Error applying noise gate: {e}")
            return audio_data
    
    def apply_compressor(
        self, 
        audio_data: np.ndarray, 
        threshold: float = 0.5,
        ratio: float = 4.0
    ) -> np.ndarray:
        """Apply audio compressor"""
        try:
            # Calculate amplitude
            amplitude = np.abs(audio_data)
            
            # Apply compression
            compressed_amplitude = np.where(
                amplitude > threshold,
                threshold + (amplitude - threshold) / ratio,
                amplitude
            )
            
            # Maintain original sign
            compressed_audio = np.sign(audio_data) * compressed_amplitude
            
            return compressed_audio
            
        except Exception as e:
            self.logger.error(f"Error applying compressor: {e}")
            return audio_data


class VideoFilters:
    """Advanced video processing filters"""
    
    def __init__(self):
        self.logger = logger
        if cv2 is None:
            self.logger.warning("OpenCV not available, video filters disabled")
    
    def apply_blur(
        self, 
        frame: np.ndarray, 
        kernel_size: int = 15
    ) -> np.ndarray:
        """Apply blur effect"""
        if cv2 is None:
            return frame
        
        try:
            return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
        except Exception as e:
            self.logger.error(f"Error applying blur: {e}")
            return frame
    
    def apply_sharpen(self, frame: np.ndarray) -> np.ndarray:
        """Apply sharpening filter"""
        if cv2 is None:
            return frame
        
        try:
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            return cv2.filter2D(frame, -1, kernel)
        except Exception as e:
            self.logger.error(f"Error applying sharpen: {e}")
            return frame
    
    def apply_sepia(self, frame: np.ndarray) -> np.ndarray:
        """Apply sepia effect"""
        if cv2 is None:
            return frame
        
        try:
            sepia_filter = np.array([
                [0.272, 0.534, 0.131],
                [0.349, 0.686, 0.168],
                [0.393, 0.769, 0.189]
            ])
            
            sepia_frame = frame.dot(sepia_filter.T)
            sepia_frame = np.clip(sepia_frame, 0, 255)
            return sepia_frame.astype(np.uint8)
        except Exception as e:
            self.logger.error(f"Error applying sepia: {e}")
            return frame
    
    def apply_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """Convert to grayscale"""
        if cv2 is None:
            return frame
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        except Exception as e:
            self.logger.error(f"Error applying grayscale: {e}")
            return frame
    
    def apply_edge_detection(self, frame: np.ndarray) -> np.ndarray:
        """Apply edge detection"""
        if cv2 is None:
            return frame
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        except Exception as e:
            self.logger.error(f"Error applying edge detection: {e}")
            return frame
    
    def apply_cartoon(self, frame: np.ndarray) -> np.ndarray:
        """Apply cartoon effect"""
        if cv2 is None:
            return frame
        
        try:
            # Reduce colors
            data = np.float32(frame).reshape((-1, 3))
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, 8, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            centers = np.uint8(centers)
            cartoon = centers[labels.flatten()].reshape(frame.shape)
            
            # Add edges
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            # Combine
            cartoon = cv2.bitwise_and(cartoon, edges)
            
            return cartoon
        except Exception as e:
            self.logger.error(f"Error applying cartoon effect: {e}")
            return frame
    
    def apply_vintage(self, frame: np.ndarray) -> np.ndarray:
        """Apply vintage effect"""
        if cv2 is None:
            return frame
        
        try:
            # Add noise
            noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
            vintage = cv2.add(frame, noise)
            
            # Reduce saturation
            hsv = cv2.cvtColor(vintage, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = hsv[:, :, 1] * 0.6  # Reduce saturation
            vintage = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            # Add vignette
            rows, cols = frame.shape[:2]
            kernel_x = cv2.getGaussianKernel(cols, cols/2)
            kernel_y = cv2.getGaussianKernel(rows, rows/2)
            kernel = kernel_y * kernel_x.T
            mask = 255 * kernel / np.linalg.norm(kernel)
            
            for i in range(3):
                vintage[:, :, i] = vintage[:, :, i] * mask
            
            return vintage.astype(np.uint8)
        except Exception as e:
            self.logger.error(f"Error applying vintage effect: {e}")
            return frame
    
    def apply_color_balance(
        self, 
        frame: np.ndarray, 
        red_gain: float = 1.0,
        green_gain: float = 1.0,
        blue_gain: float = 1.0
    ) -> np.ndarray:
        """Apply color balance"""
        try:
            balanced = frame.astype(np.float32)
            balanced[:, :, 0] *= blue_gain   # Blue channel
            balanced[:, :, 1] *= green_gain  # Green channel
            balanced[:, :, 2] *= red_gain    # Red channel
            
            return np.clip(balanced, 0, 255).astype(np.uint8)
        except Exception as e:
            self.logger.error(f"Error applying color balance: {e}")
            return frame


class FilterChain:
    """Chain multiple filters together"""
    
    def __init__(self):
        self.audio_filters = []
        self.video_filters = []
        self.logger = logger
    
    def add_audio_filter(self, filter_func, **kwargs):
        """Add audio filter to chain"""
        self.audio_filters.append((filter_func, kwargs))
    
    def add_video_filter(self, filter_func, **kwargs):
        """Add video filter to chain"""
        self.video_filters.append((filter_func, kwargs))
    
    def process_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio through filter chain"""
        result = audio_data
        
        for filter_func, kwargs in self.audio_filters:
            try:
                result = filter_func(result, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in audio filter chain: {e}")
        
        return result
    
    def process_video(self, frame: np.ndarray) -> np.ndarray:
        """Process video through filter chain"""
        result = frame
        
        for filter_func, kwargs in self.video_filters:
            try:
                result = filter_func(result, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in video filter chain: {e}")
        
        return result
    
    def clear_filters(self):
        """Clear all filters"""
        self.audio_filters.clear()
        self.video_filters.clear()