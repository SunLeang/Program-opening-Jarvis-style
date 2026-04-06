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


