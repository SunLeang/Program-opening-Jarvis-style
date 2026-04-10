import pytest
from unittest.mock import MagicMock, patch
import speech_recognition as sr
from src.audio.speech_listener import PhraseMatcher

@pytest.fixture
def mock_sr_environment():
    """Mock SpeechRecognition components to avoid hardware/network calls."""
    with patch("src.audio.speech_listener.SoundDeviceMicrophone") as MockMic, \
         patch("src.audio.speech_listener.sr.Recognizer") as MockRec:
        
        mock_mic_instance = MagicMock()
        MockMic.return_value.__enter__.return_value = mock_mic_instance
        
        mock_rec_instance = MockRec.return_value
        
        yield mock_rec_instance, mock_mic_instance

class TestPhraseMatcher:
    def test_exact_match_returns_true(self, mock_sr_environment):
        mock_rec, mock_mic = mock_sr_environment
        mock_rec.listen.return_value = MagicMock()
        mock_rec.recognize_google.return_value = "wake up"
        
        matcher = PhraseMatcher("wake up", timeout_s=3.0)
        result = matcher.listen_and_verify()
        
        assert result is True
        # Verify calibration and listen were called
        mock_rec.adjust_for_ambient_noise.assert_called_once()
        mock_rec.listen.assert_called_once()
        _, listen_kwargs = mock_rec.listen.call_args
        assert listen_kwargs["timeout"] == 3.0

    def test_fuzzy_match_returns_true(self, mock_sr_environment):
        mock_rec, _ = mock_sr_environment
        mock_rec.listen.return_value = MagicMock()
        mock_rec.recognize_google.return_value = "wake up daddys home"

        matcher = PhraseMatcher("wake up")
        assert matcher.listen_and_verify() is True

    def test_alias_match_returns_true(self, mock_sr_environment):
        mock_rec, _ = mock_sr_environment
        mock_rec.listen.return_value = MagicMock()
        mock_rec.recognize_google.return_value = "wake up"

        matcher = PhraseMatcher("wake up daddy's home", aliases=["wake up"])
        assert matcher.listen_and_verify() is True

    def test_mismatch_returns_false(self, mock_sr_environment):
        mock_rec, _ = mock_sr_environment
        mock_rec.listen.return_value = MagicMock()
        mock_rec.recognize_google.return_value = "hey jarvis"
        
        matcher = PhraseMatcher("wake up")
        assert matcher.listen_and_verify() is False

    def test_timeout_returns_false(self, mock_sr_environment):
        mock_rec, _ = mock_sr_environment
        mock_rec.listen.side_effect = sr.WaitTimeoutError("Timed out")
        
        matcher = PhraseMatcher("test")
        assert matcher.listen_and_verify() is False

    def test_network_error_returns_false(self, mock_sr_environment, caplog):
        mock_rec, _ = mock_sr_environment
        mock_rec.listen.return_value = MagicMock()
        mock_rec.recognize_google.side_effect = sr.RequestError("Connection failed")
        
        matcher = PhraseMatcher("test")
        assert matcher.listen_and_verify() is False
        assert "Google API network/request error" in caplog.text

    def test_normalization_handles_variants(self):
        # Punctuation, casing, and extra spaces should not break matching
        assert PhraseMatcher._normalize("Wake Up") == "wake up"
        assert PhraseMatcher._normalize("wake up") == "wake up"
