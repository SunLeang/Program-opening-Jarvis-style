"""Detects acoustic transients (claps) based on RMS energy threshold."""
import numpy as np

class ClapDetector:
    """Stateful detector that filters out background noise and enforces cooldown periods."""
    
    def __init__(self, threshold_db: float = -20.0) -> None:
        # Convert dBFS to linear amplitude
        self.threshold_linear = 10 ** (threshold_db / 20.0)
        self.cooldown_frames: int = 0

    def is_clap(self, audio_frame: np.ndarray) -> bool:
        """Evaluate a single frame. Returns True if spike > threshold AND cooldown expired."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset cooldown counter (used when state machine transitions back to IDLE)."""
        self.cooldown_frames = 0