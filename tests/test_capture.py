import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.audio.capture import AudioStream

@pytest.fixture
def mock_sd():
    with patch("src.audio.capture.sd") as mock:
        mock.CallbackFlags = MagicMock(input_overflow=False)
        yield mock

class TestAudioStream:
    def test_initialization_stores_params(self):
        stream = AudioStream(device_idx=2, samplerate=44100, blocksize=2048)
        assert stream.device_idx == 2
        assert stream.samplerate == 44100
        assert stream.blocksize == 2048

    def test_open_starts_stream(self, mock_sd):
        stream = AudioStream()
        stream.open()
        mock_sd.InputStream.assert_called_once()
        mock_sd.InputStream.return_value.start.assert_called_once()
        assert stream._is_running is True

    def test_yield_frames_produces_chunks(self, mock_sd):
        stream = AudioStream()
        stream.open()

        # Simulate sounddevice callback pushing data
        dummy_frame = np.random.rand(1024).astype('float32') * 0.5
        stream._callback(dummy_frame, 1024, {}, mock_sd.CallbackFlags(0))

        # Verify generator yields the exact frame
        generator = stream.yield_frames(timeout=0.1)
        result = next(generator)
        np.testing.assert_array_equal(result, dummy_frame)

    def test_close_stops_and_cleans_up(self, mock_sd):
        stream = AudioStream()
        stream.open()
        stream.close()
        
        mock_sd.InputStream.return_value.stop.assert_called_once()
        mock_sd.InputStream.return_value.close.assert_called_once()
        assert stream._is_running is False