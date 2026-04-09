"""Entry point: State machine & orchestration loop."""
import sys
import json
import logging
from pathlib import Path

from src.audio.capture import AudioStream
from src.audio.clap_detector import ClapDetector
from src.audio.speech_listener import PhraseMatcher
from src.system.audio_player import AudioPlayer
from src.system.launcher import ProgramLauncher

logger = logging.getLogger("jarvis.main")

def load_config(config_path: str) -> dict:
    """Validate JSON structure and return configuration dict."""
    raise NotImplementedError

def main() -> None:
    """
    State Flow:
      IDLE -> [Clap] -> PHRASE_READY -> [Speech Match] -> RESPONDING -> 
      PLAYING_AUDIO -> LAUNCHING_PROGRAMS -> IDLE
    """
    raise NotImplementedError

if __name__ == "__main__":
    main()