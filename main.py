"""Entry point: State machine & orchestration loop."""
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any

from src.audio.capture import AudioStream
from src.audio.clap_detector import ClapDetector
from src.audio.speech_listener import PhraseMatcher
from src.system.audio_player import AudioPlayer
from src.system.launcher import ProgramLauncher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("jarvis.main")

def load_config(config_path: str) -> dict[str, Any]:
    """Validate JSON structure and return configuration dict."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        config: dict[str, Any] = json.load(f)

    required_keys = [
        "microphone_device_index", "clap_threshold_db", "speech_timeout_s",
        "wake_phrase", "response_audio_path", "programs"
    ]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing config keys: {', '.join(missing)}")

    response_audio_path = Path(config["response_audio_path"])
    if not response_audio_path.is_absolute():
        config["response_audio_path"] = str((path.parent / response_audio_path).resolve())

    response_lead_in_s = float(config.get("response_lead_in_s", 2.0))
    if response_lead_in_s < 0:
        raise ValueError("response_lead_in_s must be >= 0")
    config["response_lead_in_s"] = response_lead_in_s

    return config

def main() -> None:
    """
    State Flow:
      IDLE (Listening) -> [Clap Spike] -> PHRASE_READY -> [Speech Match] -> 
      EXECUTING -> [Audio Play + Launch] -> IDLE (Reset & Resume)
    """
    logger.info("[JARVIS] Initializing system...")
    
    try:
        config = load_config("config.json")
    except Exception as e:
        logger.critical(f"[FATAL] Config load failed: {e}")
        sys.exit(1)

    # 1. Component Initialization
    try:
        stream = AudioStream(device_idx=config["microphone_device_index"])
        clap_detector = ClapDetector(threshold_db=config["clap_threshold_db"])
        phrase_matcher = PhraseMatcher(
            target_phrase=config["wake_phrase"],
            timeout_s=config["speech_timeout_s"],
            aliases=config.get("wake_phrase_aliases"),
        )
        audio_player = AudioPlayer(config["response_audio_path"])
        launcher = ProgramLauncher(config["programs"])
        stream.open()
    except Exception as e:
        logger.critical(f"[FATAL] Audio initialization failed: {e}")
        sys.exit(1)

    # 2. Graceful Signal Handling
    def signal_handler(sig: int, _: Any) -> None:
        logger.info(f"[JARVIS] Signal {sig} received. Shutting down...")
        stream.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, signal_handler)

    logger.info("[JARVIS] Systems online. Awaiting audio trigger...")

    try:
        while True:
            # STATE: IDLE / LISTENING
            # yield_frames is a generator that blocks until audio arrives
            for frame in stream.yield_frames(timeout=0.5):
                if clap_detector.is_clap(frame):
                    logger.info("[JARVIS] Clap detected! Switching to voice command mode...")

                    # Free the device before phrase capture to avoid multiple readers
                    stream.close()
                    try:
                        is_match = phrase_matcher.listen_and_verify(
                            device_index=config["microphone_device_index"]
                        )
                    finally:
                        stream.open()
                    
                    if is_match:
                        logger.info("[JARVIS] Wake phrase confirmed! Executing sequence...")
                        try:
                            # Start the response clip, then give it a short head start.
                            audio_player.play_background()
                            time.sleep(config["response_lead_in_s"])
                            
                            # STATE: LAUNCHING
                            launched = launcher.launch_all()
                            logger.info(f"[JARVIS] Execution complete. Opened: {launched}")
                        except Exception as e:
                            logger.error(f"[JARVIS] Sequence failed: {e}")
                    else:
                        logger.info("[JARVIS] Phrase mismatch or timeout. Returning to idle.")
                    
                    # Reset detector state and break inner loop to restart stream consumption cleanly
                    clap_detector.reset()
                    break  # Exits 'for frame' loop, returns to outer 'while True'
                    
    except Exception as e:
        logger.critical(f"[JARVIS] Unhandled runtime error: {e}")
        raise
    finally:
        stream.close()
        logger.info("[JARVIS] Graceful shutdown complete.")

if __name__ == "__main__":
    main()
