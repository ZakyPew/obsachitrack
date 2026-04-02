# Audio Event Detection System

Real-time game audio event detector for StreamTracker's AI Avatar. Detects "big moments" like achievements, deaths, and killstreaks from system audio without game APIs.

## Features

- **Low Latency**: < 500ms detection using FFT and correlation-based template matching
- **Windows Loopback Capture**: Captures system audio (not microphone)
- **Multiple Event Types**:
  - Steam achievement "ding"
  - Xbox achievement chime  
  - "YOU DIED" style death sounds
  - Killstreak announcer voices
  - Sudden audio spikes (explosions, intense moments)
- **Synthetic Templates**: Built-in synthetic signatures for common sounds
- **Custom Profiles**: Load your own reference audio for specific games

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# On Windows, you may need to install PyAudio wheel manually:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

## Quick Start

### Basic Usage (Desktop Tool Integration)

```python
from audio_detector import AudioEventDetector, detect_event, EventType
import numpy as np

# Create detector
detector = AudioEventDetector()

# Process audio buffer (numpy array)
audio_buffer = np.array(...)  # Your audio data here
event_type = detect_event(audio_buffer, detector)

if event_type:
    print(f"Detected: {event_type.name}")
```

### Real-Time Capture

```python
from audio_detector import AudioEventDetector, DetectionResult

detector = AudioEventDetector()

# List available devices
devices = detector.list_audio_devices()
for device in devices:
    print(f"[{device['index']}] {device['name']}")

# Find Stereo Mix / loopback device
loopback_index = None
for device in devices:
    if 'stereo mix' in device['name'].lower():
        loopback_index = device['index']
        break

# Start capture with callback
def on_detection(result: DetectionResult):
    print(f"🎮 {result.event_type.name}: {result.confidence:.2f}")

detector.start_capture(device_index=loopback_index, callback=on_detection)

# Run until interrupted...
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    detector.stop_capture()
```

## Windows Setup: Enable Stereo Mix

The detector uses Windows Stereo Mix to capture system audio:

1. Right-click the **speaker icon** in system tray → **Sounds**
2. Go to **Recording** tab
3. Right-click in the list → **Show Disabled Devices**
4. Find **Stereo Mix** → Right-click → **Enable**
5. Set as **Default Device** (optional)

If Stereo Mix is not available, you may need to:
- Update audio drivers
- Use a virtual audio cable (VB-Audio Virtual Cable)
- Use WASAPI loopback (advanced)

## API Reference

### `AudioEventDetector`

Main detection class.

```python
detector = AudioEventDetector(
    sample_rate=48000,      # Audio sample rate
    channels=2,             # Stereo
    chunk_size=480,         # 10ms chunks (low latency)
    profiles_dir=None       # Custom sound profiles directory
)
```

#### Methods

- `detect_event(audio_buffer) -> Optional[DetectionResult]` - Analyze audio for events
- `process_audio_chunk(chunk) -> Optional[DetectionResult]` - Process streaming audio
- `start_capture(device_index, callback)` - Start real-time capture
- `stop_capture()` - Stop capture
- `list_audio_devices() -> List[Dict]` - List available input devices
- `add_custom_profile(...) -> SoundProfile` - Add custom sound signature
- `load_profiles_from_directory(path)` - Load profiles from disk

### `DetectionResult`

```python
@dataclass
class DetectionResult:
    event_type: EventType      # Type of detected event
    confidence: float          # 0.0 to 1.0
    timestamp: float           # Seconds since start
    metadata: Dict             # Additional info (frequency, energy, etc.)
```

### `EventType`

- `STEAM_ACHIEVEMENT` - Steam achievement unlock
- `XBOX_ACHIEVEMENT` - Xbox achievement unlock
- `DEATH_SOUND` - Dark Souls / Elden Ring style death
- `KILLSTREAK_ANNOUNCER` - FPS announcer voice
- `AUDIO_SPIKE` - Sudden loud sound
- `UNKNOWN_ACHIEVEMENT` - Generic achievement

## Custom Sound Profiles

To add custom sounds for specific games:

### Method 1: Programmatic

```python
import numpy as np
from audio_detector import AudioEventDetector, EventType

# Load your reference audio file
audio_template = np.load("my_sound.npy")  # or load with librosa

# Add custom profile
detector = AudioEventDetector()
profile = detector.add_custom_profile(
    name="custom_achievement",
    event_type=EventType.UNKNOWN_ACHIEVEMENT,
    audio_template=audio_template,
    frequency_range=(1000, 4000),
    correlation_threshold=0.7
)
```

### Method 2: Sound Profiles Directory

1. Place audio files in `sound_profiles/`:
   - `my_sound.wav` (reference audio)
   - `my_sound.json` (metadata)

2. JSON format:
```json
{
  "name": "my_sound",
  "event_type": "STEAM_ACHIEVEMENT",
  "frequency_range": [1000, 4000],
  "duration_range": [0.5, 2.0],
  "correlation_threshold": 0.7,
  "energy_threshold": 0.15
}
```

3. Load profiles:
```python
detector = AudioEventDetector(profiles_dir="sound_profiles/")
```

## Detection Algorithm

The system uses multiple techniques for robust detection:

1. **Energy-based Spike Detection**: Statistical outliers in audio energy
2. **Frequency Analysis**: FFT to check frequency signature matching
3. **Template Correlation**: Normalized cross-correlation with reference sounds
4. **Spectrogram Matching**: Time-frequency correlation for complex sounds

Latency is kept low by:
- Processing 10ms chunks
- Using 500ms analysis windows
- Efficient numpy/scipy operations
- Early rejection based on energy/frequency

## Performance Tips

- Use lower `chunk_size` for lower latency (more CPU usage)
- Reduce `BUFFER_SECONDS` for faster detection (less context)
- Adjust `correlation_threshold` per profile for sensitivity
- Use `librosa` for better audio loading (optional dependency)

## Troubleshooting

### "PyAudio not available"
Install PyAudio: `pip install pyaudio` or use pre-built wheel on Windows.

### "No loopback device found"
Enable Stereo Mix in Windows sound settings (see Setup section).

### False positives
Increase `correlation_threshold` for affected profiles or add more specific frequency ranges.

### Missed detections
Lower `correlation_threshold` or load actual reference audio from the game.

## License

Part of StreamTracker project.
