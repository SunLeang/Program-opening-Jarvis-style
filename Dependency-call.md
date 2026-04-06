[User Audio]
      │
      ▼
capture.py (yields 1024-frame PCM chunks continuously)
      │
      ├──▶ clap_detector.py (RMS spike?) ──No──▶ loop back to stream
      │        │ Yes
      │        ▼
      │  speech_listener.py (5s window, listen for phrase)
      │        │ No Match
      │        └──▶ reset state, resume stream
      │        │ Match
      │        ▼
      └──────▶ audio_player.py (play response.wav) ──▶ blocks until done
                    │
                    ▼
               launcher.py (read config.json → open programs)
                    │
                    ▼
               main.py (log, reset state, resume listening loop)