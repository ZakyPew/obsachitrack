"""
Audio Event Detection System for StreamTracker's AI Avatar
Detects "big moments" from game audio in real-time using correlation-based template matching.

Usage:
    detector = AudioEventDetector()
    event = detector.detect_event(audio_buffer)  # Returns EventType or None
"""

import numpy as np
import scipy.signal as signal
from scipy.fftpack import fft
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Callable
import os
import json
import warnings

# Try to import optional dependencies
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    warnings.warn("PyAudio not available. Audio capture will be disabled.")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class EventType(Enum):
    """Types of audio events that can be detected."""
    STEAM_ACHIEVEMENT = auto()
    XBOX_ACHIEVEMENT = auto()
    DEATH_SOUND = auto()
    KILLSTREAK_ANNOUNCER = auto()
    AUDIO_SPIKE = auto()
    UNKNOWN_ACHIEVEMENT = auto()  # Generic achievement sound


@dataclass
class DetectionResult:
    """Result of an audio event detection."""
    event_type: EventType
    confidence: float  # 0.0 to 1.0
    timestamp: float   # seconds since start
    metadata: Dict     # Additional info (frequency peak, volume, etc.)


class SoundProfile:
    """Represents a reference sound signature for template matching."""
    
    def __init__(
        self,
        name: str,
        event_type: EventType,
        sample_rate: int = 48000,
        frequency_range: Tuple[float, float] = (20, 20000),
        duration_range: Tuple[float, float] = (0.1, 3.0),
        correlation_threshold: float = 0.7,
        energy_threshold: float = 0.1
    ):
        self.name = name
        self.event_type = event_type
        self.sample_rate = sample_rate
        self.frequency_range = frequency_range  # (min_hz, max_hz)
        self.duration_range = duration_range    # (min_sec, max_sec)
        self.correlation_threshold = correlation_threshold
        self.energy_threshold = energy_threshold
        self.template: Optional[np.ndarray] = None
        self.spectrogram_template: Optional[np.ndarray] = None
        
    def load_template(self, audio_data: np.ndarray):
        """Load a template audio signature."""
        self.template = audio_data.astype(np.float32)
        # Normalize
        if np.max(np.abs(self.template)) > 0:
            self.template = self.template / np.max(np.abs(self.template))
    
    def set_spectrogram_template(self, spec: np.ndarray):
        """Load a pre-computed spectrogram template."""
        self.spectrogram_template = spec.astype(np.float32)


class AudioEventDetector:
    """
    Real-time audio event detector for game audio.
    Uses FFT/spectrogram analysis and correlation-based template matching.
    """
    
    # Default sample rate for Windows loopback
    DEFAULT_SAMPLE_RATE = 48000
    
    # Chunk size for processing (10ms at 48kHz = 480 samples)
    # Lower = lower latency but more CPU usage
    CHUNK_SIZE = 480
    
    # Buffer size for analysis (500ms window)
    BUFFER_SECONDS = 0.5
    
    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = 2,
        chunk_size: int = CHUNK_SIZE,
        profiles_dir: Optional[str] = None
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.buffer_size = int(sample_rate * self.BUFFER_SECONDS)
        
        # Circular buffer for audio
        self.audio_buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self.buffer_pos = 0
        
        # Sound profiles for matching
        self.profiles: List[SoundProfile] = []
        
        # Detection state
        self.last_detection_time = 0.0
        self.detection_cooldown = 1.0  # Minimum seconds between detections
        self.current_time = 0.0
        
        # Energy tracking for spike detection
        self.energy_history = np.zeros(100)  # Last 100 energy readings
        self.energy_idx = 0
        self.energy_mean = 0.0
        self.energy_std = 0.0
        
        # PyAudio instance
        self._pa = None
        self._stream = None
        
        # Load default profiles
        self._init_default_profiles()
        
        # Load custom profiles if directory provided
        if profiles_dir:
            self.load_profiles_from_directory(profiles_dir)
    
    def _init_default_profiles(self):
        """Initialize built-in sound profiles based on known signatures."""
        
        # Steam Achievement "Ding"
        # Characteristics: High frequency chime, ~1-2 seconds, around 2000-4000 Hz
        steam_profile = SoundProfile(
            name="steam_achievement",
            event_type=EventType.STEAM_ACHIEVEMENT,
            frequency_range=(1500, 5000),
            duration_range=(0.8, 2.5),
            correlation_threshold=0.65,
            energy_threshold=0.15
        )
        self._generate_steam_template(steam_profile)
        self.profiles.append(steam_profile)
        
        # Xbox Achievement Chime
        # Characteristics: Lower pitch than Steam, around 800-1500 Hz
        xbox_profile = SoundProfile(
            name="xbox_achievement",
            event_type=EventType.XBOX_ACHIEVEMENT,
            frequency_range=(600, 2000),
            duration_range=(0.5, 2.0),
            correlation_threshold=0.65,
            energy_threshold=0.15
        )
        self._generate_xbox_template(xbox_profile)
        self.profiles.append(xbox_profile)
        
        # Death Sound (Dark Souls style)
        # Characteristics: Deep, resonant sound, 200-800 Hz, longer duration
        death_profile = SoundProfile(
            name="death_sound",
            event_type=EventType.DEATH_SOUND,
            frequency_range=(100, 1000),
            duration_range=(1.5, 4.0),
            correlation_threshold=0.60,
            energy_threshold=0.20
        )
        self._generate_death_template(death_profile)
        self.profiles.append(death_profile)
        
        # Killstreak Announcer
        # Characteristics: Voice-like, 200-3000 Hz, variable duration
        killstreak_profile = SoundProfile(
            name="killstreak_announcer",
            event_type=EventType.KILLSTREAK_ANNOUNCER,
            frequency_range=(150, 3500),
            duration_range=(0.5, 3.0),
            correlation_threshold=0.55,
            energy_threshold=0.18
        )
        self._generate_killstreak_template(killstreak_profile)
        self.profiles.append(killstreak_profile)
    
    def _generate_steam_template(self, profile: SoundProfile):
        """Generate a synthetic Steam achievement chime template."""
        duration = 1.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Steam achievement: Two-tone chime (around 2700Hz and 3500Hz)
        # First tone
        tone1 = np.sin(2 * np.pi * 2700 * t) * np.exp(-3 * t)
        # Second tone (slightly delayed and higher)
        tone2 = np.sin(2 * np.pi * 3500 * t) * np.exp(-4 * (t - 0.1)) 
        tone2[t < 0.1] = 0
        
        # Add harmonics for richness
        harmonic = 0.3 * np.sin(2 * np.pi * 5400 * t) * np.exp(-3 * t)
        
        template = (tone1 + tone2 + harmonic) / 3.0
        template *= (1 + 0.1 * np.random.randn(len(template)))  # Add slight noise
        
        profile.load_template(template)
        profile.set_spectrogram_template(self._compute_spectrogram(template))
    
    def _generate_xbox_template(self, profile: SoundProfile):
        """Generate a synthetic Xbox achievement chime template."""
        duration = 1.2
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Xbox: Lower, more resonant chime around 1100Hz with harmonic
        fundamental = np.sin(2 * np.pi * 1100 * t) * np.exp(-2 * t)
        harmonic = 0.4 * np.sin(2 * np.pi * 2200 * t) * np.exp(-2.5 * t)
        
        # Add slight pitch bend (characteristic of Xbox sound)
        pitch_bend = 1 + 0.05 * np.sin(2 * np.pi * 5 * t)
        fundamental = np.sin(2 * np.pi * 1100 * pitch_bend * t) * np.exp(-2 * t)
        
        template = (fundamental + harmonic) / 2.0
        profile.load_template(template)
        profile.set_spectrogram_template(self._compute_spectrogram(template))
    
    def _generate_death_template(self, profile: SoundProfile):
        """Generate a synthetic death sound template (Dark Souls style)."""
        duration = 2.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Deep bass impact followed by resonant decay
        # Low frequency impact
        impact = np.sin(2 * np.pi * 150 * t) * np.exp(-1 * t)
        impact[t > 0.5] *= np.exp(-2 * (t[t > 0.5] - 0.5))
        
        # Resonant drone
        drone = 0.5 * np.sin(2 * np.pi * 80 * t) * np.exp(-0.5 * t)
        
        # Metallic overtone
        metal = 0.3 * np.sin(2 * np.pi * 400 * t) * np.exp(-3 * t)
        
        # "YOU DIED" spoken word simulation (low frequency vocal pattern)
        vocal = self._simulate_vocal_pattern(t, [200, 250, 180], [0.3, 0.4, 0.5])
        
        template = (impact + drone + metal + 0.5 * vocal) / 3.0
        profile.load_template(template)
        profile.set_spectrogram_template(self._compute_spectrogram(template))
    
    def _generate_killstreak_template(self, profile: SoundProfile):
        """Generate a synthetic killstreak announcer template."""
        duration = 1.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Announcer voice: Mid-range frequencies with formant structure
        # Simulate "Double Kill!" or similar with formants
        f1 = self._simulate_vocal_pattern(t, [500, 600, 400], [0.2, 0.3, 0.4])
        f2 = self._simulate_vocal_pattern(t, [1200, 1400, 1000], [0.2, 0.3, 0.4]) * 0.6
        f3 = self._simulate_vocal_pattern(t, [2500, 2800, 2200], [0.2, 0.3, 0.4]) * 0.3
        
        template = (f1 + f2 + f3) / 2.0
        profile.load_template(template)
        profile.set_spectrogram_template(self._compute_spectrogram(template))
    
    def _simulate_vocal_pattern(
        self, 
        t: np.ndarray, 
        frequencies: List[float], 
        durations: List[float]
    ) -> np.ndarray:
        """Simulate a vocal pattern with given frequencies and durations."""
        result = np.zeros_like(t)
        current_time = 0.0
        
        for freq, dur in zip(frequencies, durations):
            mask = (t >= current_time) & (t < current_time + dur)
            if np.any(mask):
                # Add vibrato for natural voice sound
                vibrato = 1 + 0.03 * np.sin(2 * np.pi * 5 * t[mask])
                result[mask] = np.sin(2 * np.pi * freq * vibrato * t[mask])
                # Envelope
                envelope = np.sin(np.pi * (t[mask] - current_time) / dur)
                result[mask] *= envelope
            current_time += dur
        
        return result
    
    def _compute_spectrogram(
        self, 
        audio: np.ndarray, 
        n_fft: int = 2048,
        hop_length: int = 512
    ) -> np.ndarray:
        """Compute magnitude spectrogram of audio."""
        if LIBROSA_AVAILABLE:
            return np.abs(librosa.stft(audio, n_fft=n_fft, hop_length=hop_length))
        else:
            # Fallback using scipy
            f, t, Zxx = signal.stft(audio, fs=self.sample_rate, nperseg=n_fft, noverlap=n_fft-hop_length)
            return np.abs(Zxx)
    
    def _compute_mfcc(self, audio: np.ndarray, n_mfcc: int = 13) -> np.ndarray:
        """Compute MFCC features for voice detection."""
        if LIBROSA_AVAILABLE:
            return librosa.feature.mfcc(
                y=audio, 
                sr=self.sample_rate, 
                n_mfcc=n_mfcc,
                n_fft=2048,
                hop_length=512
            )
        return np.array([])
    
    def add_custom_profile(
        self,
        name: str,
        event_type: EventType,
        audio_template: Optional[np.ndarray] = None,
        frequency_range: Tuple[float, float] = (20, 20000),
        correlation_threshold: float = 0.7
    ) -> SoundProfile:
        """Add a custom sound profile."""
        profile = SoundProfile(
            name=name,
            event_type=event_type,
            frequency_range=frequency_range,
            correlation_threshold=correlation_threshold
        )
        
        if audio_template is not None:
            profile.load_template(audio_template)
            profile.set_spectrogram_template(self._compute_spectrogram(audio_template))
        
        self.profiles.append(profile)
        return profile
    
    def load_profiles_from_directory(self, directory: str):
        """Load sound profiles from a directory."""
        if not os.path.exists(directory):
            return
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                self._load_profile_json(os.path.join(directory, filename))
            elif filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
                self._load_profile_audio(os.path.join(directory, filename))
    
    def _load_profile_json(self, filepath: str):
        """Load a profile from JSON metadata."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            event_type = EventType[data.get('event_type', 'UNKNOWN_ACHIEVEMENT')]
            profile = SoundProfile(
                name=data.get('name', os.path.basename(filepath)),
                event_type=event_type,
                frequency_range=tuple(data.get('frequency_range', [20, 20000])),
                duration_range=tuple(data.get('duration_range', [0.1, 3.0])),
                correlation_threshold=data.get('correlation_threshold', 0.7),
                energy_threshold=data.get('energy_threshold', 0.1)
            )
            
            # Try to load associated audio file
            base_name = os.path.splitext(filepath)[0]
            for ext in ['.wav', '.mp3', '.ogg', '.flac']:
                audio_path = base_name + ext
                if os.path.exists(audio_path):
                    self._load_audio_into_profile(audio_path, profile)
                    break
            
            self.profiles.append(profile)
        except Exception as e:
            print(f"Failed to load profile {filepath}: {e}")
    
    def _load_profile_audio(self, filepath: str):
        """Load a profile from an audio file (auto-detect type from filename)."""
        try:
            filename = os.path.basename(filepath).lower()
            
            # Auto-detect event type from filename
            if 'steam' in filename:
                event_type = EventType.STEAM_ACHIEVEMENT
            elif 'xbox' in filename:
                event_type = EventType.XBOX_ACHIEVEMENT
            elif 'death' in filename or 'died' in filename:
                event_type = EventType.DEATH_SOUND
            elif 'kill' in filename or 'streak' in filename:
                event_type = EventType.KILLSTREAK_ANNOUNCER
            else:
                event_type = EventType.UNKNOWN_ACHIEVEMENT
            
            profile = SoundProfile(
                name=os.path.splitext(filename)[0],
                event_type=event_type
            )
            
            self._load_audio_into_profile(filepath, profile)
            self.profiles.append(profile)
            
        except Exception as e:
            print(f"Failed to load audio profile {filepath}: {e}")
    
    def _load_audio_into_profile(self, filepath: str, profile: SoundProfile):
        """Load audio file into a profile using available libraries."""
        if LIBROSA_AVAILABLE:
            audio, sr = librosa.load(filepath, sr=self.sample_rate, mono=True)
            profile.load_template(audio)
            profile.set_spectrogram_template(self._compute_spectrogram(audio))
        else:
            # Fallback: try scipy.io.wavfile for WAV files
            try:
                from scipy.io import wavfile
                sr, audio = wavfile.read(filepath)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)  # Convert to mono
                # Resample if needed
                if sr != self.sample_rate:
                    from scipy import signal as sp_signal
                    audio = sp_signal.resample(audio, int(len(audio) * self.sample_rate / sr))
                profile.load_template(audio.astype(np.float32))
                profile.set_spectrogram_template(self._compute_spectrogram(audio))
            except Exception as e:
                print(f"Could not load {filepath}: {e}")
    
    def process_audio_chunk(self, chunk: np.ndarray) -> Optional[DetectionResult]:
        """
        Process a new audio chunk and detect events.
        
        Args:
            chunk: Audio samples (mono or stereo, will be converted to mono)
            
        Returns:
            DetectionResult if an event is detected, None otherwise
        """
        # Convert to mono if stereo
        if chunk.ndim > 1:
            chunk = chunk.mean(axis=1)
        
        # Normalize to float32
        chunk = chunk.astype(np.float32)
        if np.max(np.abs(chunk)) > 0:
            chunk = chunk / np.max(np.abs(chunk))
        
        # Add to circular buffer
        chunk_len = len(chunk)
        if self.buffer_pos + chunk_len <= self.buffer_size:
            self.audio_buffer[self.buffer_pos:self.buffer_pos + chunk_len] = chunk
        else:
            # Wrap around
            first_part = self.buffer_size - self.buffer_pos
            self.audio_buffer[self.buffer_pos:] = chunk[:first_part]
            self.audio_buffer[:chunk_len - first_part] = chunk[first_part:]
        
        self.buffer_pos = (self.buffer_pos + chunk_len) % self.buffer_size
        self.current_time += chunk_len / self.sample_rate
        
        # Run detection
        return self.detect_event(self.audio_buffer.copy())
    
    def detect_event(self, audio_buffer: np.ndarray) -> Optional[DetectionResult]:
        """
        Main detection entry point - analyze audio buffer for events.
        
        Args:
            audio_buffer: Numpy array of audio samples (mono, float32)
            
        Returns:
            DetectionResult if an event is detected, None otherwise
        """
        # Ensure correct format
        audio_buffer = audio_buffer.astype(np.float32)
        if np.max(np.abs(audio_buffer)) > 0:
            audio_buffer = audio_buffer / np.max(np.abs(audio_buffer))
        
        # Update energy statistics
        current_energy = np.mean(audio_buffer ** 2)
        self.energy_history[self.energy_idx] = current_energy
        self.energy_idx = (self.energy_idx + 1) % len(self.energy_history)
        self.energy_mean = np.mean(self.energy_history)
        self.energy_std = np.std(self.energy_history) + 1e-10
        
        # Check for audio spike
        spike_result = self._detect_spike(audio_buffer, current_energy)
        if spike_result:
            return spike_result
        
        # Check cooldown
        if self.current_time - self.last_detection_time < self.detection_cooldown:
            return None
        
        # Analyze frequency content
        fft_result = fft(audio_buffer)
        freqs = np.fft.fftfreq(len(audio_buffer), 1/self.sample_rate)
        magnitudes = np.abs(fft_result)
        
        # Only look at positive frequencies
        positive_mask = freqs > 0
        freqs = freqs[positive_mask]
        magnitudes = magnitudes[positive_mask]
        
        best_match = None
        best_confidence = 0.0
        
        # Try to match against each profile
        for profile in self.profiles:
            confidence = self._match_profile(audio_buffer, freqs, magnitudes, profile)
            if confidence > profile.correlation_threshold and confidence > best_confidence:
                best_confidence = confidence
                best_match = profile
        
        if best_match:
            self.last_detection_time = self.current_time
            
            # Find dominant frequency
            peak_idx = np.argmax(magnitudes)
            dominant_freq = freqs[peak_idx]
            
            return DetectionResult(
                event_type=best_match.event_type,
                confidence=best_confidence,
                timestamp=self.current_time,
                metadata={
                    'profile_name': best_match.name,
                    'dominant_frequency': float(dominant_freq),
                    'energy': float(current_energy),
                    'profile_threshold': best_match.correlation_threshold
                }
            )
        
        return None
    
    def _detect_spike(
        self, 
        audio_buffer: np.ndarray, 
        current_energy: float
    ) -> Optional[DetectionResult]:
        """Detect sudden audio spikes (explosions, intense moments)."""
        # Spike detection: energy > mean + 4 * std
        spike_threshold = self.energy_mean + 4 * self.energy_std
        
        if current_energy > spike_threshold and current_energy > 0.05:
            # Check cooldown for spikes (shorter than other events)
            if self.current_time - self.last_detection_time < 0.3:
                return None
            
            self.last_detection_time = self.current_time
            
            # Calculate spike magnitude in standard deviations
            z_score = (current_energy - self.energy_mean) / self.energy_std
            
            return DetectionResult(
                event_type=EventType.AUDIO_SPIKE,
                confidence=min(z_score / 10, 1.0),  # Cap at 1.0
                timestamp=self.current_time,
                metadata={
                    'spike_magnitude_db': float(10 * np.log10(current_energy + 1e-10)),
                    'z_score': float(z_score),
                    'energy': float(current_energy)
                }
            )
        
        return None
    
    def _match_profile(
        self,
        audio_buffer: np.ndarray,
        freqs: np.ndarray,
        magnitudes: np.ndarray,
        profile: SoundProfile
    ) -> float:
        """
        Match audio buffer against a sound profile.
        Returns confidence score (0.0 to 1.0).
        """
        confidence = 0.0
        
        # Check frequency range match
        freq_mask = (freqs >= profile.frequency_range[0]) & (freqs <= profile.frequency_range[1])
        freq_energy = np.sum(magnitudes[freq_mask])
        total_energy = np.sum(magnitudes) + 1e-10
        freq_ratio = freq_energy / total_energy
        
        # Frequency match contributes to confidence
        confidence += freq_ratio * 0.3
        
        # Check energy threshold
        buffer_energy = np.mean(audio_buffer ** 2)
        if buffer_energy < profile.energy_threshold:
            return 0.0
        
        # Template correlation if available
        if profile.template is not None:
            corr_score = self._correlation_match(audio_buffer, profile.template)
            confidence += corr_score * 0.5
        
        # Spectrogram correlation if available
        if profile.spectrogram_template is not None:
            spec = self._compute_spectrogram(audio_buffer[:len(profile.template)])
            if spec.shape == profile.spectrogram_template.shape:
                spec_corr = self._matrix_correlation(spec, profile.spectrogram_template)
                confidence += spec_corr * 0.2
        
        return min(confidence, 1.0)
    
    def _correlation_match(self, buffer: np.ndarray, template: np.ndarray) -> float:
        """Compute normalized cross-correlation between buffer and template."""
        # Use shorter length
        length = min(len(buffer), len(template))
        buffer_short = buffer[:length]
        template_short = template[:length]
        
        # Normalize both
        buffer_norm = buffer_short - np.mean(buffer_short)
        template_norm = template_short - np.mean(template_short)
        
        buffer_std = np.std(buffer_norm) + 1e-10
        template_std = np.std(template_norm) + 1e-10
        
        buffer_norm = buffer_norm / buffer_std
        template_norm = template_norm / template_std
        
        # Correlation
        correlation = np.abs(np.correlate(buffer_norm, template_norm, mode='valid'))
        
        return float(np.max(correlation)) / length if len(correlation) > 0 else 0.0
    
    def _matrix_correlation(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute correlation between two matrices."""
        a_flat = a.flatten()
        b_flat = b.flatten()
        
        a_norm = a_flat - np.mean(a_flat)
        b_norm = b_flat - np.mean(b_flat)
        
        a_std = np.std(a_norm) + 1e-10
        b_std = np.std(b_norm) + 1e-10
        
        correlation = np.abs(np.sum(a_norm * b_norm)) / (a_std * b_std * len(a_flat))
        return float(correlation)
    
    def start_capture(
        self, 
        device_index: Optional[int] = None,
        callback: Optional[Callable[[DetectionResult], None]] = None
    ):
        """
        Start capturing system audio (Windows loopback).
        
        Args:
            device_index: PyAudio device index (None for default)
            callback: Optional callback function called on each detection
        """
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio is not available. Cannot start capture.")
        
        self._pa = pyaudio.PyAudio()
        
        # Open stream
        self._stream = self._pa.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback(callback)
        )
        
        self._stream.start_stream()
    
    def _audio_callback(self, callback: Optional[Callable]):
        """Create PyAudio callback function."""
        def callback_wrapper(in_data, frame_count, time_info, status):
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Process the chunk
            result = self.process_audio_chunk(audio_data)
            
            if result and callback:
                callback(result)
            
            return (in_data, pyaudio.paContinue)
        
        return callback_wrapper
    
    def stop_capture(self):
        """Stop audio capture."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        
        if self._pa:
            self._pa.terminate()
            self._pa = None
    
    def list_audio_devices(self) -> List[Dict]:
        """List available audio input devices."""
        if not PYAUDIO_AVAILABLE:
            return []
        
        pa = pyaudio.PyAudio()
        devices = []
        
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': info['defaultSampleRate']
                })
        
        pa.terminate()
        return devices
    
    def save_profile(self, profile: SoundProfile, directory: str):
        """Save a sound profile to disk."""
        os.makedirs(directory, exist_ok=True)
        
        # Save metadata
        metadata = {
            'name': profile.name,
            'event_type': profile.event_type.name,
            'frequency_range': list(profile.frequency_range),
            'duration_range': list(profile.duration_range),
            'correlation_threshold': profile.correlation_threshold,
            'energy_threshold': profile.energy_threshold
        }
        
        json_path = os.path.join(directory, f"{profile.name}.json")
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save template audio
        if profile.template is not None:
            wav_path = os.path.join(directory, f"{profile.name}.wav")
            self._save_wav(wav_path, profile.template)
    
    def _save_wav(self, filepath: str, audio: np.ndarray):
        """Save audio to WAV file."""
        try:
            from scipy.io import wavfile
            # Convert to int16
            audio_int16 = (audio * 32767).astype(np.int16)
            wavfile.write(filepath, self.sample_rate, audio_int16)
        except Exception as e:
            print(f"Failed to save WAV: {e}")


# Convenience function for desktop tool integration
def detect_event(audio_buffer: np.ndarray, detector: Optional[AudioEventDetector] = None) -> Optional[EventType]:
    """
    Simple interface for the desktop tool.
    
    Args:
        audio_buffer: Numpy array of audio samples
        detector: Optional existing detector instance (creates new if None)
        
    Returns:
        EventType if detected, None otherwise
    """
    if detector is None:
        detector = AudioEventDetector()
    
    result = detector.detect_event(audio_buffer)
    if result:
        return result.event_type
    return None


# Example usage and testing
if __name__ == "__main__":
    import time
    
    print("Audio Event Detector - Test Mode")
    print("=" * 50)
    
    # Create detector
    detector = AudioEventDetector()
    
    # List audio devices
    print("\nAvailable audio input devices:")
    devices = detector.list_audio_devices()
    for device in devices:
        print(f"  [{device['index']}] {device['name']} ({device['channels']}ch @ {device['sample_rate']}Hz)")
    
    # Look for Stereo Mix / loopback device
    loopback_index = None
    for device in devices:
        if 'stereo mix' in device['name'].lower() or 'loopback' in device['name'].lower():
            loopback_index = device['index']
            print(f"\n✓ Found loopback device: {device['name']} (index {loopback_index})")
            break
    
    if loopback_index is None:
        print("\n⚠ No loopback device found. You may need to enable Stereo Mix in Windows.")
        print("  Testing with synthetic audio instead...")
        
        # Generate synthetic test audio
        sample_rate = 48000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a Steam-like achievement sound
        tone1 = np.sin(2 * np.pi * 2700 * t) * np.exp(-3 * t)
        tone2 = np.sin(2 * np.pi * 3500 * t) * np.exp(-4 * (t - 0.1))
        tone2[t < 0.1] = 0
        test_audio = (tone1 + tone2) / 2
        
        print("\nTesting with synthetic Steam achievement sound...")
        result = detector.detect_event(test_audio)
        
        if result:
            print(f"✓ Detected: {result.event_type.name} (confidence: {result.confidence:.2f})")
            print(f"  Metadata: {result.metadata}")
        else:
            print("✗ No event detected")
    else:
        print("\nStarting real-time detection (press Ctrl+C to stop)...")
        
        def on_detection(result: DetectionResult):
            print(f"\n🎮 DETECTED: {result.event_type.name}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Time: {result.timestamp:.2f}s")
            print(f"   Metadata: {result.metadata}")
        
        try:
            detector.start_capture(device_index=loopback_index, callback=on_detection)
            
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nStopping...")
        finally:
            detector.stop_capture()
    
    print("\nDone!")
