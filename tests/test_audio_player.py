import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.system.audio_player import AudioPlayer

# Minimal valid WAV header (44 bytes) + 2 bytes of silence data
# This allows us to test file reading without needing a real audio file.
DUMMY_WAV_CONTENT = (
    b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00'
    b'\x80>\x00\x00\x02\x00\x10\x00data\x04\x00\x00\x00\x00\x00'
)

class TestAudioPlayer:
    def test_plays_valid_wav(self, tmp_path):
        """Verify play() invokes blocking playback on a valid file."""
        # Create temporary dummy WAV file
        wav_file = tmp_path / "response.wav"
        wav_file.write_bytes(DUMMY_WAV_CONTENT)

        # Mock WAV decoding + playback to avoid hardware usage in tests
        with patch('src.system.audio_player.AudioPlayer._read_wav_float32') as mock_read_wav, \
             patch('src.system.audio_player.sd.play') as mock_play, \
             patch('src.system.audio_player.sd.stop') as mock_stop, \
             patch('src.system.audio_player.sd.wait') as mock_wait:
            mock_read_wav.return_value = (MagicMock(), 16000)

            player = AudioPlayer(str(wav_file))
            player.play()

            mock_read_wav.assert_called_once_with(wav_file)
            mock_stop.assert_called_once()
            mock_play.assert_called_once_with(mock_read_wav.return_value[0], 16000)
            mock_wait.assert_called_once()

    def test_play_background_starts_without_waiting(self, tmp_path):
        """Verify background playback starts immediately and does not wait."""
        wav_file = tmp_path / "response.wav"
        wav_file.write_bytes(DUMMY_WAV_CONTENT)

        with patch('src.system.audio_player.AudioPlayer._read_wav_float32') as mock_read_wav, \
             patch('src.system.audio_player.sd.play') as mock_play, \
             patch('src.system.audio_player.sd.stop') as mock_stop, \
             patch('src.system.audio_player.sd.wait') as mock_wait:
            mock_read_wav.return_value = (MagicMock(), 16000)

            player = AudioPlayer(str(wav_file))
            player.play_background()

            mock_read_wav.assert_called_once_with(wav_file)
            mock_stop.assert_called_once()
            mock_play.assert_called_once_with(mock_read_wav.return_value[0], 16000)
            mock_wait.assert_not_called()

    def test_missing_file_raises_file_not_found(self):
        """Verify FileNotFoundError is raised for missing paths."""
        player = AudioPlayer("/nonexistent/path.wav")
        with pytest.raises(FileNotFoundError):
            player.play()

    def test_hardware_failure_raises_runtime_error(self, tmp_path):
        """Verify hardware errors are caught and re-raised as RuntimeError."""
        wav_file = tmp_path / "bad.wav"
        wav_file.write_bytes(DUMMY_WAV_CONTENT)

        with patch('src.system.audio_player.AudioPlayer._read_wav_float32') as mock_read_wav, \
             patch('src.system.audio_player.sd.play') as mock_play, \
             patch('src.system.audio_player.sd.stop'), \
             patch('src.system.audio_player.sd.wait'):
            mock_read_wav.return_value = (MagicMock(), 16000)
            mock_play.side_effect = Exception("No device")

            player = AudioPlayer(str(wav_file))
            with pytest.raises(RuntimeError, match="Unexpected playback error"):
                player.play()
