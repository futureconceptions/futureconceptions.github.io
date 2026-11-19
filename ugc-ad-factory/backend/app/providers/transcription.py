"""Speech-to-text for dialogue-accuracy QA. LetzAI offers no transcription
endpoint, so this is optional: `faster_whisper` runs locally when the package
is installed (not part of the default image); otherwise QA marks dialogue
accuracy as 'not_checked' instead of pretending it passed."""
from __future__ import annotations

import difflib
import re


class NoTranscription:
    name = "none"

    def available(self) -> bool:
        return False

    def transcribe(self, audio_path: str, language: str | None = None) -> str:  # pragma: no cover
        raise RuntimeError("no transcription provider configured")


class FasterWhisperTranscription:
    name = "faster_whisper"

    def __init__(self, model_size: str = "base"):
        self._model = None
        self.model_size = model_size

    def available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        from faster_whisper import WhisperModel
        if self._model is None:
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        segments, _ = self._model.transcribe(audio_path, language=language)
        return " ".join(s.text.strip() for s in segments)


def normalize_words(text: str) -> list[str]:
    return re.findall(r"[\wäöüß']+", text.lower())


def dialogue_similarity(expected: str, actual: str) -> float:
    """Word-level similarity (0..1). The reference workflow treated ≥0.86 as a match."""
    a, b = normalize_words(expected), normalize_words(actual)
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(a=a, b=b).ratio()
