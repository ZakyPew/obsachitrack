#!/usr/bin/env python3
"""
Example integration for StreamTracker Desktop Tool
Shows how to integrate audio detection with the desktop application.
"""

import sys
import time
import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass

# Import the audio detector
from audio_detector import AudioEventDetector, EventType, DetectionResult


@dataclass
class GameEvent:
    """Event data structure for StreamTracker."""
    event_type: str
    timestamp: float
    confidence: float
    metadata: dict


class StreamTrackerAudio:
    """
    Audio integration module for StreamTracker Desktop Tool.
    
    This class provides a simple interface for the desktop tool to:
    - Start/stop audio capture
    - Receive game events via callback
    - Configure detection sensitivity
    """
    
    def __init__(self):
        self.detector: Optional[AudioEventDetector] = None
        self._event_callback: Optional[Callable[[GameEvent], None]] = None
        self._running = False
        
        # Event type mapping to StreamTracker format
        self._event_map = {
            EventType.STEAM_ACHIEVEMENT: "achievement",
            EventType.XBOX_ACHIEVEMENT: "achievement", 
            EventType.UNKNOWN_ACHIEVEMENT: "achievement",
            EventType.DEATH_SOUND: "death",
            EventType.KILLSTREAK_ANNOUNCER: "killstreak",
            EventType.AUDIO_SPIKE: "spike"
        }
    
    def initialize(self, profiles_dir: str = "sound_profiles/") -> bool:
        """
        Initialize the audio detector.
        
        Args:
            profiles_dir: Directory containing custom sound profiles
            
        Returns:
            True if initialization successful
        """
        try:
            self.detector = AudioEventDetector(profiles_dir=profiles_dir)
            print(f"✓ Audio detector initialized with {len(self.detector.profiles)} profiles")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize audio detector: {e}")
            return False
    
    def set_event_callback(self, callback: Callable[[GameEvent], None]):
        """
        Set callback function to receive game events.
        
        Args:
            callback: Function called with GameEvent on each detection
        """
        self._event_callback = callback
    
    def start(self, device_index: Optional[int] = None) -> bool:
        """
        Start audio capture and detection.
        
        Args:
            device_index: Audio device index (None for auto-detect loopback)
            
        Returns:
            True if started successfully
        """
        if not self.detector:
            print("✗ Detector not initialized. Call initialize() first.")
            return False
        
        # Auto-detect loopback device if not specified
        if device_index is None:
            device_index = self._find_loopback_device()
            if device_index is None:
                print("✗ No loopback device found. Enable Stereo Mix in Windows.")
                return False
        
        try:
            self.detector.start_capture(
                device_index=device_index,
                callback=self._on_detection
            )
            self._running = True
            print(f"✓ Audio capture started on device {device_index}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start capture: {e}")
            return False
    
    def stop(self):
        """Stop audio capture."""
        if self.detector:
            self.detector.stop_capture()
        self._running = False
        print("✓ Audio capture stopped")
    
    def _find_loopback_device(self) -> Optional[int]:
        """Find Windows Stereo Mix / loopback device."""
        devices = self.detector.list_audio_devices()
        
        for device in devices:
            name = device['name'].lower()
            if any(keyword in name for keyword in ['stereo mix', 'loopback', 'what u hear', 'wave out']):
                print(f"✓ Found loopback device: {device['name']} (index {device['index']})")
                return device['index']
        
        return None
    
    def _on_detection(self, result: DetectionResult):
        """Internal callback when detection occurs."""
        # Convert to GameEvent format
        game_event = GameEvent(
            event_type=self._event_map.get(result.event_type, "unknown"),
            timestamp=result.timestamp,
            confidence=result.confidence,
            metadata={
                'original_type': result.event_type.name,
                **result.metadata
            }
        )
        
        # Call user callback
        if self._event_callback:
            self._event_callback(game_event)
        
        # Also print to console for debugging
        self._print_event(game_event)
    
    def _print_event(self, event: GameEvent):
        """Print event to console with emoji."""
        emoji_map = {
            "achievement": "🏆",
            "death": "💀",
            "killstreak": "🔥",
            "spike": "💥",
            "unknown": "❓"
        }
        
        emoji = emoji_map.get(event.event_type, "🎮")
        print(f"{emoji} [{event.timestamp:.2f}s] {event.event_type.upper()} "
              f"(confidence: {event.confidence:.2f})")
    
    def set_sensitivity(self, event_type: str, threshold: float):
        """
        Adjust detection sensitivity for an event type.
        
        Args:
            event_type: Event type name (achievement, death, killstreak, spike)
            threshold: Correlation threshold (0.0 to 1.0, higher = less sensitive)
        """
        if not self.detector:
            return
        
        # Map back to EventType
        reverse_map = {
            "achievement": [EventType.STEAM_ACHIEVEMENT, EventType.XBOX_ACHIEVEMENT],
            "death": [EventType.DEATH_SOUND],
            "killstreak": [EventType.KILLSTREAK_ANNOUNCER],
            "spike": [EventType.AUDIO_SPIKE]
        }
        
        target_types = reverse_map.get(event_type, [])
        
        for profile in self.detector.profiles:
            if profile.event_type in target_types:
                old_threshold = profile.correlation_threshold
                profile.correlation_threshold = threshold
                print(f"  {profile.name}: threshold {old_threshold:.2f} → {threshold:.2f}")
    
    @property
    def is_running(self) -> bool:
        """Check if audio capture is running."""
        return self._running
    
    def list_devices(self) -> list:
        """List available audio input devices."""
        if not self.detector:
            return []
        return self.detector.list_audio_devices()


def example_manual_detection():
    """Example: Manual detection from audio buffer (for testing)."""
    print("\n" + "=" * 60)
    print("Example: Manual Detection from Audio Buffer")
    print("=" * 60)
    
    # Create detector
    detector = AudioEventDetector()
    
    # Generate synthetic test audio (Steam achievement)
    sample_rate = 48000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create Steam-like sound
    tone1 = np.sin(2 * np.pi * 2700 * t) * np.exp(-3 * t)
    tone2 = np.sin(2 * np.pi * 3500 * t) * np.exp(-4 * (t - 0.1))
    tone2[t < 0.1] = 0
    test_audio = (tone1 + tone2) / 2
    
    # Detect event
    result = detector.detect_event(test_audio)
    
    if result:
        print(f"✓ Detected: {result.event_type.name}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Metadata: {result.metadata}")
    else:
        print("✗ No event detected")


def example_streaming_detection():
    """Example: Real-time streaming detection."""
    print("\n" + "=" * 60)
    print("Example: Real-time Streaming Detection")
    print("=" * 60)
    
    # Create integration
    audio = StreamTrackerAudio()
    
    # Initialize
    if not audio.initialize():
        return
    
    # Set up event handler
    def on_event(event: GameEvent):
        # This is where you'd send to your AI Avatar or UI
        print(f"  [TO AVATAR] Event: {event.event_type}, Conf: {event.confidence:.2f}")
    
    audio.set_event_callback(on_event)
    
    # List devices
    print("\nAvailable devices:")
    for device in audio.list_devices():
        print(f"  [{device['index']}] {device['name']}")
    
    # Adjust sensitivity (optional)
    print("\nAdjusting sensitivity...")
    audio.set_sensitivity("achievement", 0.60)  # More sensitive
    audio.set_sensitivity("death", 0.65)
    
    # Start capture
    print("\nStarting capture (Ctrl+C to stop)...")
    if audio.start():
        try:
            while audio.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            audio.stop()


def example_simple_api():
    """Example: Simple API usage for desktop tool."""
    print("\n" + "=" * 60)
    print("Example: Simple API Usage")
    print("=" * 60)
    
    from audio_detector import detect_event
    
    # Your desktop tool receives audio buffer from somewhere
    # (e.g., from a separate capture thread)
    sample_rate = 48000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simulate incoming audio buffer
    audio_buffer = np.random.randn(len(t)) * 0.1  # Noise
    
    # Mix in a death sound
    death_tone = np.sin(2 * np.pi * 150 * t) * np.exp(-0.5 * t) * 0.8
    audio_buffer += death_tone
    
    # Simple detection call
    event_type = detect_event(audio_buffer)
    
    if event_type:
        print(f"✓ Desktop tool detected: {event_type.name}")
    else:
        print("✗ No detection")


if __name__ == "__main__":
    print("StreamTracker Audio Detection - Examples")
    
    # Run examples
    example_manual_detection()
    example_simple_api()
    
    # Uncomment to test real-time capture:
    # example_streaming_detection()
    
    print("\n✓ Examples complete!")
