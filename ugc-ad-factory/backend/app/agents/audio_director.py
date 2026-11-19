"""Agent 6 - Audio Director: native model audio vs. synthesized speech.

Native audio is preferred when the selected LetzAI video model generates
synchronized audio (Seedance 2.5, Kling 4, Gemini Omni, Flux 3...). Otherwise
speech is synthesized with LetzAI POST /audios (kind=speech), using the
creator's stored voice preset for identity consistency across ads."""
from __future__ import annotations

import re

from app.providers.base import MediaRequest, VideoModelInfo

_NUM_DE = {"0": "null", "1": "eins", "2": "zwei", "3": "drei", "4": "vier", "5": "fünf", "6": "sechs",
           "7": "sieben", "8": "acht", "9": "neun", "10": "zehn", "12": "zwölf", "20": "zwanzig",
           "24": "vierundzwanzig", "30": "dreißig", "50": "fünfzig", "100": "hundert"}


def choose_audio_mode(info: VideoModelInfo, requested: str | None) -> str:
    if requested in ("native", "tts"):
        if requested == "native" and not info.native_audio:
            return "tts"
        return requested
    return "native" if info.native_audio else "tts"


def prepare_speech_text(text: str, language: str) -> str:
    """Light TTS normalization: German small numbers as words, % spelled out,
    collapse whitespace. Keeps the words otherwise identical to the script."""
    t = re.sub(r"\s+", " ", text).strip()
    if language == "de":
        t = re.sub(r"(\d+)\s?%", lambda m: f"{_NUM_DE.get(m.group(1), m.group(1))} Prozent", t)
        t = re.sub(r"\b(\d{1,3})\b", lambda m: _NUM_DE.get(m.group(1), m.group(1)), t)
    else:
        t = re.sub(r"(\d+)\s?%", r"\1 percent", t)
    return t


def speech_request(*, text: str, voice: str | None, language: str, model: str | None) -> MediaRequest:
    return MediaRequest(kind="speech", text=prepare_speech_text(text, language), voice=voice or "friendly-young",
                        language=language, model=model,
                        extra={"direction": "casual, natural conversational delivery with small pauses"})


def music_request(*, mood: str, duration: int) -> MediaRequest:
    return MediaRequest(kind="music", prompt=f"Light, unobtrusive instrumental background bed for a social video: {mood}. "
                                             "No vocals, steady low energy, no sudden drops.",
                        duration=max(10, min(300, int(5 * round(duration / 5)) or 10)))
