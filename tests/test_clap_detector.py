import numpy as np
import pytest
from src.audio.clap_detector import ClapDetector

@pytest.fixture
def detector():
    # -26dB threshold -> ~0.05 peak amplitude
    # 16kHz sample rate, 1s cooldown (16000 frames)
    return ClapDetector(threshold_db=-26.0, samplerate=16000, cooldown_seconds=1.0)


def make_clap_frame(peak: float = 0.7) -> np.ndarray:
    frame = np.zeros(1024, dtype=np.float32)
    frame[512:516] = peak
    return frame

class TestClapDetector:
    def test_silence_returns_false(self, detector):
        """Zero-amplitude frame should never trigger."""
        silence = np.zeros(1024)
        assert detector.is_clap(silence) is False

    def test_spike_exceeding_threshold_returns_true(self, detector):
        """A short transient spike should trigger detection."""
        clap = make_clap_frame()
        assert detector.is_clap(clap) is True
        # Verify cooldown was triggered
        assert detector._frames_remaining > 0

    def test_cooldown_prevents_retrigger(self, detector):
        """Rapid successive spikes should ignore all but the first."""
        clap = make_clap_frame()
        
        # First clap -> True
        assert detector.is_clap(clap) is True
        
        # Immediate second clap (during cooldown) -> False
        assert detector.is_clap(clap) is False
        
        # Force reset
        detector.reset()
        assert detector._frames_remaining == 0
        
        # Third clap (after reset) -> True
        assert detector.is_clap(clap) is True

    def test_subthreshold_noise_returns_false(self, detector):
        """Broad low-level noise should not look like a clap transient."""
        quiet_noise = np.full(1024, 0.02, dtype=np.float32)
        assert detector.is_clap(quiet_noise) is False
