from typing import Generator, Optional
import numpy as np
import sounddevice as sd

class AudioStream:
    """Yields fixed-size PCM audio chunks from the default or specified microphone."""
    
    def __init__(self, device_idx: Optional[int] = None, 
                 samplerate: int = 16000, channels: int = 1) -> None:
        self.samplerate = samplerate
        self.channels = channels
        self.device_idx = device_idx
        self._stream: Optional[sd.InputStream] = None

    def open(self) -> None:
        """Initialize non-blocking input stream.
        
        Raises:
            sd.PortAudioError: If device is unavailable or invalid.
        """
        raise NotImplementedError

    def yield_frames(self, frame_size: int = 1024) -> Generator[np.ndarray, None, None]:
        """Continuously yield normalized audio frames.
        
        Blocks until stream is closed or interrupted.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Safely stop the audio stream."""
        raise NotImplementedError