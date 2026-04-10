"""Continuous microphone stream provider."""
from typing import Generator, Optional
import queue
import logging
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
        class CallbackFlags:
            input_overflow = False

        class InputStream:
            def __init__(self, *args, **kwargs):
                raise RuntimeError(_PORTAUDIO_HELP)

    sd = _MissingSoundDevice()

logger = logging.getLogger(__name__)

class AudioStream:
    """Yields fixed-size PCM audio chunks from the microphone via a thread-safe queue."""

    def __init__(self, device_idx: Optional[int] = None,
                 samplerate: int = 16000, channels: int = 1,
                 blocksize: int = 1024) -> None:
        self.samplerate = samplerate
        self.channels = channels
        self.device_idx = device_idx
        self.blocksize = blocksize
        self._stream: Optional[sd.InputStream] = None
        self._buffer: queue.Queue[np.ndarray] = queue.Queue(maxsize=10)
        self._is_running = False

    def _callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
        if status.input_overflow:
            logger.warning("Audio input buffer overflow. Dropping frame.")
        try:
            self._buffer.put_nowait(indata.copy())
        except queue.Full:
            logger.warning("Audio frame queue full. Dropping oldest buffered frame.")
            try:
                self._buffer.get_nowait()
            except queue.Empty:
                pass
            self._buffer.put_nowait(indata.copy())

    def open(self) -> None:
        """Initialize and start the PortAudio input stream."""
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            device=self.device_idx,
            channels=self.channels,
            dtype='float32',
            blocksize=self.blocksize,
            callback=self._callback
        )
        self._stream.start()
        self._is_running = True
        logger.info(f"Audio stream initialized [SR={self.samplerate}Hz, Blk={self.blocksize}]")

    def yield_frames(self, timeout: float = 1.0) -> Generator[np.ndarray, None, None]:
        """Continuously yield normalized audio frames. Blocks until stream closes."""
        if not self._is_running:
            raise RuntimeError("Stream not open. Call open() first.")
        while self._is_running:
            try:
                yield self._buffer.get(timeout=timeout)
            except queue.Empty:
                # Timeout means no new audio yet. Loop continues.
                continue

    def close(self) -> None:
        """Safely stop the audio stream and release hardware."""
        if self._stream:
            self._is_running = False
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Audio stream closed.")
