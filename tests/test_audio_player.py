import pytest
import os
# from src.system.audio_player import AudioPlayer

class TestAudioPlayer:
    def test_plays_valid_wav(self, tmp_path) -> None:
        """Create dummy WAV, assert play() completes without error."""
        pass

    def test_missing_file_raises_file_not_found(self) -> None:
        """Pass invalid path, expect FileNotFoundError."""
        pass