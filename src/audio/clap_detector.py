import logging

import numpy as np

logger = logging.getLogger(__name__)


class ClapDetector:
    """Transient-based clap detector with an adaptive noise floor."""

    def __init__(
        self,
        threshold_db: float = -26.0,
        samplerate: int = 16000,
        cooldown_seconds: float = 1.0,
        min_transient_ratio: float = 4.0,
        min_crest_factor: float = 2.5,
        noise_floor_alpha: float = 0.08,
    ) -> None:
        """Initialize with detection parameters.
        
        Args:
            threshold_db: Minimum instantaneous peak level (dBFS) to trigger.
            samplerate: Audio sample rate, used to convert seconds to frame counts.
            cooldown_seconds: Ignore audio for this duration after a detection.
        """
        self.samplerate = samplerate
        self.threshold_linear = 10 ** (threshold_db / 20.0)
        self.cooldown_frames = int(samplerate * cooldown_seconds)
        self.min_transient_ratio = min_transient_ratio
        self.min_crest_factor = min_crest_factor
        self.noise_floor_alpha = noise_floor_alpha
        self._frames_remaining = 0
        self._noise_floor = max(self.threshold_linear / 8.0, 1e-4)

    def is_clap(self, audio_frame: np.ndarray) -> bool:
        """Return True when a frame looks like a sharp transient above room noise."""
        frame = np.asarray(audio_frame, dtype=np.float32).reshape(-1)
        if frame.size == 0:
            return False

        if self._frames_remaining > 0:
            self._frames_remaining = max(0, self._frames_remaining - frame.size)
            return False

        abs_frame = np.abs(frame)
        peak = float(np.max(abs_frame))
        rms = float(np.sqrt(np.mean(np.square(frame))))
        crest_factor = peak / max(rms, 1e-6)
        transient_ratio = peak / max(self._noise_floor, 1e-4)

        if (
            peak >= self.threshold_linear
            and transient_ratio >= self.min_transient_ratio
            and crest_factor >= self.min_crest_factor
        ):
            logger.debug(
                "Clap transient detected: peak=%.3f noise_floor=%.3f ratio=%.2f crest=%.2f",
                peak,
                self._noise_floor,
                transient_ratio,
                crest_factor,
            )
            self._trigger_cooldown()
            return True

        if peak < self.threshold_linear * 1.5:
            self._noise_floor = (
                (1.0 - self.noise_floor_alpha) * self._noise_floor
                + self.noise_floor_alpha * max(rms, 1e-4)
            )

        return False

    def _trigger_cooldown(self) -> None:
        """Set the internal cooldown timer to ignore subsequent noise."""
        self._frames_remaining = self.cooldown_frames
        logger.info("[CLAP DETECTED] Locking out audio for ~1s to prevent echo.")

    def reset(self) -> None:
        """Reset cooldown counter (used when state machine transitions back to IDLE)."""
        self._frames_remaining = 0
