import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from main import load_config, main

@pytest.fixture
def valid_config():
    return {
        "microphone_device_index": None,
        "clap_threshold_db": -26.0,
        "speech_timeout_s": 2.0,
        "wake_phrase": "wake up daddys home",
        "response_audio_path": "./dummy.wav",
        "response_lead_in_s": 2.0,
        "programs": [{"name": "VSCode", "windows_cmd": "code", "linux_cmd": "code"}]
    }

class TestConfigLoader:
    def test_load_valid_config(self, tmp_path, valid_config):
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(valid_config))
        result = load_config(str(cfg))
        expected = dict(valid_config)
        expected["response_audio_path"] = str((tmp_path / "dummy.wav").resolve())
        assert result == expected

    def test_missing_keys_raises_value_error(self, tmp_path, valid_config):
        del valid_config["programs"]
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(valid_config))
        with pytest.raises(ValueError, match="Missing config keys"):
            load_config(str(cfg))

    def test_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.json")

    def test_default_lead_in_is_applied(self, tmp_path, valid_config):
        valid_config.pop("response_lead_in_s")
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(valid_config))
        result = load_config(str(cfg))
        assert result["response_lead_in_s"] == 2.0

    def test_negative_lead_in_raises_value_error(self, tmp_path, valid_config):
        valid_config["response_lead_in_s"] = -1
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(valid_config))
        with pytest.raises(ValueError, match="response_lead_in_s must be >= 0"):
            load_config(str(cfg))

class TestMainOrchestration:
    @patch("main.ProgramLauncher")
    @patch("main.AudioPlayer")
    @patch("main.PhraseMatcher")
    @patch("main.ClapDetector")
    @patch("main.AudioStream")
    @patch("main.load_config")
    @patch("main.time.sleep")
    def test_happy_path_clap_then_launch(self, mock_sleep, mock_load, mock_stream_cls, mock_det_cls, 
                                          mock_match_cls, mock_player_cls, mock_launcher_cls, valid_config):
        mock_load.return_value = valid_config
        
        mock_stream = MagicMock()
        mock_stream_cls.return_value = mock_stream
        mock_detector = MagicMock()
        mock_det_cls.return_value = mock_detector
        mock_matcher = MagicMock()
        mock_matcher.listen_and_verify.return_value = True
        mock_match_cls.return_value = mock_matcher
        mock_player_cls.return_value = MagicMock()
        mock_launcher = MagicMock()
        mock_launcher_cls.return_value = mock_launcher
        mock_launcher.launch_all.return_value = ["VSCode"]

        mock_stream.yield_frames.return_value = iter([MagicMock()])
        mock_detector.is_clap.return_value = True
        mock_detector.reset.side_effect = SystemExit

        with patch("main.signal.signal"):
            with pytest.raises(SystemExit):
                main()

        assert mock_stream.open.call_count == 2
        mock_detector.reset.assert_called_once()
        mock_matcher.listen_and_verify.assert_called_once()
        mock_player_cls.return_value.play_background.assert_called_once()
        mock_player_cls.return_value.play.assert_not_called()
        mock_sleep.assert_called_once_with(2.0)
        mock_launcher.launch_all.assert_called_once()
        assert mock_stream.close.call_count == 2

    @patch("main.ProgramLauncher")
    @patch("main.AudioPlayer")
    @patch("main.PhraseMatcher")
    @patch("main.ClapDetector")
    @patch("main.AudioStream")
    @patch("main.load_config")
    @patch("main.time.sleep")
    def test_reset_on_mismatch(self, mock_sleep, mock_load, mock_stream_cls, mock_det_cls, 
                               mock_match_cls, mock_player_cls, mock_launcher_cls, valid_config):
        mock_load.return_value = valid_config
        mock_stream = MagicMock()
        mock_stream_cls.return_value = mock_stream
        mock_detector = MagicMock()
        mock_det_cls.return_value = mock_detector
        mock_matcher = MagicMock()
        mock_matcher.listen_and_verify.return_value = False  # Mismatch
        mock_match_cls.return_value = mock_matcher
        mock_player_cls.return_value = MagicMock()
        mock_launcher = MagicMock()
        mock_launcher_cls.return_value = mock_launcher

        # Trigger clap immediately
        mock_stream.yield_frames.return_value = iter([MagicMock()])
        mock_detector.is_clap.return_value = True
        mock_detector.reset.side_effect = SystemExit

        with patch("main.signal.signal"):
            with pytest.raises(SystemExit):
                main()

        mock_player_cls.return_value.play_background.assert_not_called()
        mock_player_cls.return_value.play.assert_not_called()
        mock_sleep.assert_not_called()
        mock_launcher.launch_all.assert_not_called()
        mock_detector.reset.assert_called_once()
        assert mock_stream.open.call_count == 2
        assert mock_stream.close.call_count == 2
