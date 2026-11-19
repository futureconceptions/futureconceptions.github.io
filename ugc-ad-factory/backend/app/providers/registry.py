"""Builds provider instances from settings (single place to swap vendors)."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.providers.lipsync import NoLipSync, WaveSpeedLipSync
from app.providers.llm import AnthropicLLM, HeuristicLLM
from app.providers.transcription import FasterWhisperTranscription, NoTranscription

_overrides: dict = {}


def override(**providers) -> None:
    """Test hook: override(media=..., llm=..., lipsync=..., transcription=...)."""
    _overrides.update(providers)


def clear_overrides() -> None:
    _overrides.clear()
    _media.cache_clear()
    _llm.cache_clear()
    _lipsync.cache_clear()


@lru_cache
def _media():
    s = get_settings()
    if s.media_provider == "letzai":
        from app.providers.letzai.adapter import LetzAIProvider
        return LetzAIProvider()
    from app.providers.mock import MockMediaProvider
    return MockMediaProvider()


@lru_cache
def _llm():
    s = get_settings()
    if s.llm_provider == "anthropic" and s.anthropic_api_key:
        return AnthropicLLM()
    return HeuristicLLM()


@lru_cache
def _lipsync():
    s = get_settings()
    if s.lipsync_provider == "wavespeed":
        return WaveSpeedLipSync()
    if s.lipsync_provider == "mock":
        from app.providers.mock import MockLipSyncProvider
        return MockLipSyncProvider()
    return NoLipSync()


def media_provider():
    return _overrides.get("media") or _media()


def llm_provider():
    return _overrides.get("llm") or _llm()


def lipsync_provider():
    return _overrides.get("lipsync") or _lipsync()


def transcription_provider():
    if "transcription" in _overrides:
        return _overrides["transcription"]
    if get_settings().transcription_provider == "faster_whisper":
        t = FasterWhisperTranscription()
        if t.available():
            return t
    return NoTranscription()
