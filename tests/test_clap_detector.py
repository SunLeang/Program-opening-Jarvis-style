import numpy as np
import pytest
# from src.audio.clap_detector import ClapDetector

class TestClapDetector:
    def test_silence_returns_false(self) -> None:
        """Zero-amplitude frame should never trigger."""
        pass

    def test_spike_exceeding_threshold_returns_true(self) -> None:
        """Sudden high-RMS frame should trigger if cooldown is 0."""
        pass

    def test_cooldown_prevents_retrigger(self) -> None:
        """Rapid successive spikes should ignore all but the first."""
        pass