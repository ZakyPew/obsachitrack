#!/usr/bin/env python3
"""
Unit tests for Audio Event Detection System
Run with: python -m pytest test_audio_detector.py -v
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_detector import (
    AudioEventDetector,
    SoundProfile,
    EventType,
    DetectionResult,
    detect_event
)


class TestAudioEventDetector(unittest.TestCase):
    """Test cases for the audio event detector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = AudioEventDetector()
        self.sample_rate = 48000
    
    def test_detector_initialization(self):
        """Test that detector initializes correctly."""
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.sample_rate, 48000)
        self.assertEqual(len(self.detector.profiles), 4)  # Built-in profiles
    
    def test_steam_achievement_detection(self):
        """Test detection of synthetic Steam achievement sound."""
        # Generate Steam-like achievement sound
        duration = 2.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        tone1 = np.sin(2 * np.pi * 2700 * t) * np.exp(-3 * t)
        tone2 = np.sin(2 * np.pi * 3500 * t) * np.exp(-4 * (t - 0.1))
        tone2[t < 0.1] = 0
        audio = (tone1 + tone2) / 2
        
        result = self.detector.detect_event(audio)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type, EventType.STEAM_ACHIEVEMENT)
        self.assertGreater(result.confidence, 0.5)
    
    def test_xbox_achievement_detection(self):
        """Test detection of synthetic Xbox achievement sound."""
        duration = 1.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Xbox-like lower frequency chime
        fundamental = np.sin(2 * np.pi * 1100 * t) * np.exp(-2 * t)
        harmonic = 0.4 * np.sin(2 * np.pi * 2200 * t) * np.exp(-2.5 * t)
        audio = (fundamental + harmonic) / 2
        
        result = self.detector.detect_event(audio)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type, EventType.XBOX_ACHIEVEMENT)
    
    def test_death_sound_detection(self):
        """Test detection of synthetic death sound."""
        duration = 2.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Dark Souls-like death sound
        impact = np.sin(2 * np.pi * 150 * t) * np.exp(-1 * t)
        impact[t > 0.5] *= np.exp(-2 * (t[t > 0.5] - 0.5))
        drone = 0.5 * np.sin(2 * np.pi * 80 * t) * np.exp(-0.5 * t)
        audio = (impact + drone) / 2
        
        result = self.detector.detect_event(audio)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type, EventType.DEATH_SOUND)
    
    def test_audio_spike_detection(self):
        """Test detection of sudden audio spike."""
        # Create quiet audio followed by spike
        duration = 1.0
        samples = int(self.sample_rate * duration)
        
        # Quiet noise
        audio = np.random.randn(samples) * 0.01
        
        # Sudden spike in the middle
        spike_start = samples // 2
        spike_duration = int(0.1 * self.sample_rate)
        audio[spike_start:spike_start+spike_duration] += 0.8
        
        # Process multiple chunks to build energy history
        chunk_size = self.detector.chunk_size
        result = None
        for i in range(0, len(audio) - chunk_size, chunk_size):
            chunk = audio[i:i+chunk_size]
            result = self.detector.process_audio_chunk(chunk)
            if result:
                break
        
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type, EventType.AUDIO_SPIKE)
    
    def test_no_detection_on_silence(self):
        """Test that silence doesn't trigger detection."""
        audio = np.zeros(self.sample_rate)  # 1 second of silence
        result = self.detector.detect_event(audio)
        self.assertIsNone(result)
    
    def test_no_detection_on_noise(self):
        """Test that random noise doesn't trigger detection."""
        audio = np.random.randn(self.sample_rate) * 0.1
        result = self.detector.detect_event(audio)
        self.assertIsNone(result)
    
    def test_simple_api(self):
        """Test the simple detect_event API."""
        # Generate Steam sound
        duration = 2.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        tone1 = np.sin(2 * np.pi * 2700 * t) * np.exp(-3 * t)
        tone2 = np.sin(2 * np.pi * 3500 * t) * np.exp(-4 * (t - 0.1))
        tone2[t < 0.1] = 0
        audio = (tone1 + tone2) / 2
        
        event_type = detect_event(audio)
        
        self.assertIsNotNone(event_type)
        self.assertEqual(event_type, EventType.STEAM_ACHIEVEMENT)
    
    def test_spectrogram_computation(self):
        """Test that spectrogram computation works."""
        audio = np.random.randn(self.sample_rate * 2)
        spec = self.detector._compute_spectrogram(audio)
        
        self.assertIsInstance(spec, np.ndarray)
        self.assertGreater(spec.shape[0], 0)
        self.assertGreater(spec.shape[1], 0)
    
    def test_custom_profile_addition(self):
        """Test adding custom profiles."""
        initial_count = len(self.detector.profiles)
        
        # Create custom template
        template = np.sin(2 * np.pi * 1000 * np.linspace(0, 1, self.sample_rate))
        
        profile = self.detector.add_custom_profile(
            name="custom_sound",
            event_type=EventType.UNKNOWN_ACHIEVEMENT,
            audio_template=template,
            frequency_range=(500, 1500),
            correlation_threshold=0.6
        )
        
        self.assertEqual(len(self.detector.profiles), initial_count + 1)
        self.assertEqual(profile.name, "custom_sound")
        self.assertIsNotNone(profile.template)
    
    def test_detection_result_structure(self):
        """Test DetectionResult dataclass."""
        result = DetectionResult(
            event_type=EventType.STEAM_ACHIEVEMENT,
            confidence=0.85,
            timestamp=1.5,
            metadata={'test': 'value'}
        )
        
        self.assertEqual(result.event_type, EventType.STEAM_ACHIEVEMENT)
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.timestamp, 1.5)
        self.assertEqual(result.metadata['test'], 'value')


class TestSoundProfile(unittest.TestCase):
    """Test cases for SoundProfile class."""
    
    def test_profile_creation(self):
        """Test creating a sound profile."""
        profile = SoundProfile(
            name="test_profile",
            event_type=EventType.STEAM_ACHIEVEMENT,
            frequency_range=(1000, 3000),
            correlation_threshold=0.7
        )
        
        self.assertEqual(profile.name, "test_profile")
        self.assertEqual(profile.event_type, EventType.STEAM_ACHIEVEMENT)
        self.assertEqual(profile.frequency_range, (1000, 3000))
        self.assertEqual(profile.correlation_threshold, 0.7)
    
    def test_template_loading(self):
        """Test loading audio template."""
        profile = SoundProfile(
            name="test",
            event_type=EventType.STEAM_ACHIEVEMENT
        )
        
        template = np.array([0.1, 0.2, 0.3, 0.2, 0.1])
        profile.load_template(template)
        
        self.assertIsNotNone(profile.template)
        np.testing.assert_array_almost_equal(profile.template, template / 0.3)


class TestEventTypes(unittest.TestCase):
    """Test EventType enum."""
    
    def test_event_type_values(self):
        """Test that all event types are defined."""
        self.assertIsNotNone(EventType.STEAM_ACHIEVEMENT)
        self.assertIsNotNone(EventType.XBOX_ACHIEVEMENT)
        self.assertIsNotNone(EventType.DEATH_SOUND)
        self.assertIsNotNone(EventType.KILLSTREAK_ANNOUNCER)
        self.assertIsNotNone(EventType.AUDIO_SPIKE)
        self.assertIsNotNone(EventType.UNKNOWN_ACHIEVEMENT)


def run_benchmark():
    """Run performance benchmark."""
    print("\n" + "=" * 60)
    print("Performance Benchmark")
    print("=" * 60)
    
    import time
    
    detector = AudioEventDetector()
    sample_rate = 48000
    
    # Generate test audio
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    tone1 = np.sin(2 * np.pi * 2700 * t) * np.exp(-3 * t)
    tone2 = np.sin(2 * np.pi * 3500 * t) * np.exp(-4 * (t - 0.1))
    tone2[t < 0.1] = 0
    audio = (tone1 + tone2) / 2
    
    # Benchmark detection
    iterations = 100
    start = time.time()
    
    for _ in range(iterations):
        detector.detect_event(audio)
    
    elapsed = time.time() - start
    avg_time = (elapsed / iterations) * 1000  # Convert to ms
    
    print(f"Iterations: {iterations}")
    print(f"Total time: {elapsed:.3f}s")
    print(f"Average detection time: {avg_time:.2f}ms")
    print(f"Target: < 500ms")
    print(f"Status: {'✓ PASS' if avg_time < 500 else '✗ FAIL'}")


if __name__ == "__main__":
    # Run unit tests
    unittest.main(exit=False, verbosity=2)
    
    # Run benchmark
    run_benchmark()
