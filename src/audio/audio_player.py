from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AudioPlayer:
    """Loads and plays a .wav file synchronously (blocks until finished)."""
    
    def __init__(self, wav_path: str) -> None:
        self.wav_path = Path(wav_path)

    def play(self) -> None:
        """Validate path exists, load waveform, and block playback.
        
        Raises:
            FileNotFoundError: If WAV file is missing.
            RuntimeError: If playback hardware initialization fails.
        """
        raise NotImplementedError