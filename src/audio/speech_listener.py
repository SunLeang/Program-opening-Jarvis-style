"""Listens for a specific wake phrase within a configurable timeout window."""
from typing import Optional
import speech_recognition as sr

class PhraseMatcher:
    """Wraps SpeechRecognition with explicit timeout and phrase normalization."""
    
    def __init__(self, target_phrase: str, timeout_s: float = 5.0, 
                 phrase_time_limit: float = 3.0) -> None:
        self.target_phrase = target_phrase.lower().strip().replace("  ", " ")
        self.recognizer = sr.Recognizer()
        self.timeout_s = timeout_s
        self.phrase_time_limit = phrase_time_limit

    def listen_and_verify(self, device_index: Optional[int] = None) -> bool:
        """Open mic, wait for speech, and return True only if phrase matches.
        
        Catches sr.UnknownValueError and sr.RequestError gracefully.
        """
        raise NotImplementedError