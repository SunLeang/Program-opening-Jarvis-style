"""WAV playback engine."""
import logging
import wave
from pathlib import Path

import numpy as np

_PORTAUDIO_HELP = (
    "PortAudio library not found. On Debian/Ubuntu run: "
    "sudo apt update && sudo apt install -y libportaudio2"
)

try:
    import sounddevice as sd
    _SOUNDDEVICE_ERROR = None
except (ImportError, OSError) as exc:
    _SOUNDDEVICE_ERROR = exc

    class _MissingSoundDevice:
        class PortAudioError(Exception):
            pass

        @staticmethod
        def play(*args, **kwargs):
            raise RuntimeError(_PORTAUDIO_HELP)

        @staticmethod
        def stop(*args, **kwargs):
            return None

        @staticmethod
        def wait(*args, **kwargs):
            return None

    sd = _MissingSoundDevice()

logger = logging.getLogger(__name__)

class AudioPlayer:
    """Loads and plays a .wav file, either blocking or in the background."""
    
    def __init__(self, wav_path: str) -> None:
        self.wav_path = Path(wav_path)

    def _load_audio(self):
        if not self.wav_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.wav_path.resolve()}")

        audio_data, sample_rate = self._read_wav_float32(self.wav_path)
        return audio_data, sample_rate

    def play(self) -> None:
        """Validate path exists, load waveform, and block playback.
        
        Raises:
            FileNotFoundError: If WAV file is missing.
            RuntimeError: If playback hardware initialization fails.
        """
        try:
            logger.info(f"[AUDIO] Playing: {self.wav_path.name}")
            audio_data, sample_rate = self._load_audio()

            # Force a clean playback session and wait until the device finishes.
            sd.stop()
            sd.play(audio_data, sample_rate)
            sd.wait()

        except sd.PortAudioError as e:
            logger.error(f"[AUDIO] Playback failed: {e}")
            raise RuntimeError(f"Audio hardware error: {e}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[AUDIO] Unexpected error: {e}")
            raise RuntimeError(f"Unexpected playback error: {e}")

    def play_background(self) -> None:
        """Validate path exists, start playback, and return immediately."""
        try:
            logger.info(f"[AUDIO] Playing in background: {self.wav_path.name}")
            audio_data, sample_rate = self._load_audio()

            sd.stop()
            sd.play(audio_data, sample_rate)
        except sd.PortAudioError as e:
            logger.error(f"[AUDIO] Playback failed: {e}")
            raise RuntimeError(f"Audio hardware error: {e}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[AUDIO] Unexpected error: {e}")
            raise RuntimeError(f"Unexpected playback error: {e}")

    @staticmethod
    def _read_wav_float32(wav_path: Path):
        """Load WAV as float32 in [-1, 1] with shape (samples,) or (samples, channels)."""
        with wave.open(str(wav_path), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            raw_frames = wav_file.readframes(wav_file.getnframes())

        if sample_width == 1:
            # 8-bit PCM is unsigned.
            audio = np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32)
            audio = (audio - 128.0) / 128.0
        elif sample_width == 2:
            audio = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 4:
            audio = np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

        if channels > 1:
            audio = audio.reshape(-1, channels)

        return audio, sample_rate
