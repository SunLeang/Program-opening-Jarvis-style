Program-opening-Jarvis-style/
├── main.py                 # Entry point & orchestration loop
├── config.json             # User-editable program list, audio paths, thresholds
├── requirements.txt        # Pinned cross-platform dependencies
├── src/
│   ├── audio/
│   │   ├── capture.py      # Microphone stream provider
│   │   ├── clap_detector.py# Short-term energy spike detection
│   │   └── speech_listener.py # Wake-phrase matcher (activated post-clap)
│   └── system/
│       ├── audio_player.py # Synchronous .wav playback
│       └── launcher.py     # Cross-platform program opener
└── tests/
    ├── test_clap_detector.py
    ├── test_launcher.py
    └── test_audio_player.py

Quick start:
1) Run ./setup_venv.sh
2) Activate the environment:
    source .venv/bin/activate
3) Start the app:
    python main.py

Notes:
- Speech capture uses `sounddevice` and `SpeechRecognition`; `PyAudio` is no longer required.
- If you want the current shell activated automatically, run:
    source ./setup_venv.sh

Linux note (PortAudio runtime):
If setup or startup fails with "PortAudio library not found", install:

sudo apt update
sudo apt install -y libportaudio2

