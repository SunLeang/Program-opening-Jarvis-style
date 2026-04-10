"""Listens for a specific wake phrase within a configurable timeout window."""
import difflib
import logging
import re
from typing import Optional

import speech_recognition as sr

_PORTAUDIO_HELP = (
    "PortAudio library not found. On Debian/Ubuntu run: "
    "sudo apt update && sudo apt install -y libportaudio2"
)

try:
    import sounddevice as sd
    _SOUNDDEVICE_ERROR = None
except (ImportError, OSError) as exc:
    _SOUNDDEVICE_ERROR = exc
    sd = None

logger = logging.getLogger(__name__)


class _SoundDeviceStream:
    """Adapt `sounddevice.RawInputStream` to SpeechRecognition's stream interface."""

    def __init__(self, stream: "sd.RawInputStream") -> None:
        self._stream = stream

    def read(self, size: int) -> bytes:
        data, overflowed = self._stream.read(size)
        if overflowed:
            logger.warning("[LISTENER] Input overflow while reading microphone audio.")
        return bytes(data)


class SoundDeviceMicrophone(sr.AudioSource):
    """SpeechRecognition-compatible microphone source backed by sounddevice."""

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
    ) -> None:
        if _SOUNDDEVICE_ERROR is not None:
            raise RuntimeError(_PORTAUDIO_HELP) from _SOUNDDEVICE_ERROR

        self.device_index = device_index
        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk_size
        self.SAMPLE_WIDTH = 2
        self.stream: Optional[_SoundDeviceStream] = None
        self._raw_stream: Optional["sd.RawInputStream"] = None

    def __enter__(self) -> "SoundDeviceMicrophone":
        self._raw_stream = sd.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.CHUNK,
            device=self.device_index,
            channels=1,
            dtype="int16",
        )
        self._raw_stream.start()
        self.stream = _SoundDeviceStream(self._raw_stream)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._raw_stream is not None:
            self._raw_stream.stop()
            self._raw_stream.close()
        self.stream = None
        self._raw_stream = None

class PhraseMatcher:
    """Wraps SpeechRecognition with explicit timeout, ambient calibration, and phrase normalization."""
    
    def __init__(
        self,
        target_phrase: str,
        timeout_s: float = 5.0,
        phrase_time_limit: float = 3.0,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        ambient_duration: float = 0.3,
        aliases: Optional[list[str]] = None,
    ) -> None:
        self.target_phrase = self._normalize(target_phrase)
        alias_list = aliases or []
        normalized_aliases = [self._normalize(alias) for alias in alias_list if alias.strip()]
        self.accepted_phrases = [self.target_phrase, *normalized_aliases]
        self.recognizer = sr.Recognizer()
        # Dynamic threshold adapts to room noise level at runtime
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6
        self.recognizer.non_speaking_duration = 0.25
        self.timeout_s = timeout_s
        self.phrase_time_limit = phrase_time_limit
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.ambient_duration = ambient_duration

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, strip, remove punctuation, collapse spaces for robust matching."""
        text = text.lower().strip()
        # Remove non-alphanumeric characters (handles apostrophes, commas, etc.)
        text = re.sub(r'[^\w\s]', '', text)
        return re.sub(r'\s+', ' ', text)

    def _is_phrase_match(self, recognized_text: str) -> bool:
        normalized = self._normalize(recognized_text)
        spoken_tokens = set(normalized.split())

        for candidate in self.accepted_phrases:
            if normalized == candidate:
                logger.info("[LISTENER] Heard exact wake phrase: '%s'", normalized)
                return True

            candidate_tokens = set(candidate.split())
            if candidate_tokens and candidate_tokens.issubset(spoken_tokens):
                logger.info(
                    "[LISTENER] Heard phrase containing wake phrase: '%s' -> '%s'",
                    normalized,
                    candidate,
                )
                return True

            similarity = difflib.SequenceMatcher(
                None,
                normalized,
                candidate,
            ).ratio()
            token_overlap = (
                len(candidate_tokens & spoken_tokens) / len(candidate_tokens)
                if candidate_tokens
                else 0.0
            )
            if similarity >= 0.82 or (
                token_overlap >= 0.75 and similarity >= 0.68
            ):
                logger.info(
                    "[LISTENER] Heard fuzzy wake phrase: '%s' -> '%s' (similarity=%.2f overlap=%.2f)",
                    normalized,
                    candidate,
                    similarity,
                    token_overlap,
                )
                return True

        logger.info("[LISTENER] Heard non-matching phrase: '%s'", normalized)
        return False

    def listen_and_verify(self, device_index: Optional[int] = None) -> bool:
        """Open mic, calibrate noise, listen, and return True only if phrase matches.
        
        Handles speech timeout, recognition failures, and network errors gracefully.
        """
        try:
            # Context manager ensures mic is properly closed even on error
            with SoundDeviceMicrophone(
                device_index=device_index,
                sample_rate=self.sample_rate,
                chunk_size=self.chunk_size,
            ) as source:
                # Short calibration prevents false triggers from sudden ambient spikes
                logger.info(
                    "[LISTENER] Calibrating background noise (%.1fs)...",
                    self.ambient_duration,
                )
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self.ambient_duration,
                )
                
                logger.info(f"[LISTENER] Listening for '{self.target_phrase}'...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.timeout_s, 
                    phrase_time_limit=self.phrase_time_limit
                )

            # Google Web Speech API (free, no API key, requires internet)
            recognized_text = self.recognizer.recognize_google(audio)
            return self._is_phrase_match(recognized_text)

        except sr.WaitTimeoutError:
            logger.warning("[LISTENER] Timeout: No speech detected in window.")
            return False
        except sr.UnknownValueError:
            logger.warning("[LISTENER] Could not parse speech audio.")
            return False
        except sr.RequestError as e:
            logger.error(f"[LISTENER] Google API network/request error: {e}")
            return False
        except Exception as e:
            logger.error(f"[LISTENER] Unexpected hardware/runtime error: {e}")
            return False
