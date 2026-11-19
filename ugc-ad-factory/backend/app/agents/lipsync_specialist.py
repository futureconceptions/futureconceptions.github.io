"""Agent 7 - Lip-Sync Specialist.

Decides per scene:
  native     - the video model produced the dialogue itself (already synced)
  sync       - external lip-sync provider re-animates the mouth to TTS audio
  voiceover  - no lip-sync provider: TTS is laid over footage directed as a
               non-speaking demo shot (recorded in the QA report)
LetzAI exposes no standalone lip-sync endpoint (verified in its public API).
"""
from __future__ import annotations


def decide(*, audio_source: str | None, has_dialogue: bool, clip_has_audio: bool, lipsync_available: bool) -> str:
    if not has_dialogue:
        return "none"
    if audio_source == "native" and clip_has_audio:
        return "native"
    if lipsync_available:
        return "sync"
    return "voiceover"
