"""LetzAI model catalogue: live from GET /catalog, falling back to the bundled
snapshot of https://letz.ai/docs/models.json. Used for model discovery,
duration/resolution limits and credit estimates."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Callable

from app.providers.base import VideoModelInfo

SNAPSHOT = Path(__file__).with_name("catalog_snapshot.json")


class Catalog:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.models: dict[str, dict[str, Any]] = data.get("models", {})
        self._alias: dict[str, str] = {}
        for key, m in self.models.items():
            self._alias[key.lower()] = key
            for a in m.get("aliases", []) or []:
                self._alias.setdefault(str(a).lower(), key)
            fe = m.get("frontend") or {}
            if fe.get("baseModel"):
                self._alias.setdefault(str(fe["baseModel"]).lower(), key)

    @property
    def version(self) -> str | None:
        return self.data.get("version")

    def resolve(self, name: str | None) -> str | None:
        if not name:
            return None
        return self._alias.get(name.lower())

    def get(self, name: str | None) -> dict[str, Any] | None:
        key = self.resolve(name)
        return self.models.get(key) if key else None

    # ---------------------------------------------------------- discovery
    def list(self, capability: str | None = None, active_only: bool = True) -> list[dict[str, Any]]:
        out = []
        for key, m in self.models.items():
            caps = m.get("capabilities", {})
            if capability and capability not in caps:
                continue
            if active_only and not m.get("active"):
                continue
            out.append({"key": key, "displayName": m.get("displayName"),
                        "status": m.get("status"), "useWhen": m.get("useWhen"),
                        "rating": m.get("rating"), "capabilities": caps})
        return out

    def video_model(self, name: str) -> VideoModelInfo:
        key = self.resolve(name)
        if not key or "video" not in self.models[key].get("capabilities", {}):
            raise KeyError(f"unknown LetzAI video model: {name}")
        m = self.models[key]
        v = m["capabilities"]["video"]
        dur = v.get("duration") or {}
        refs = v.get("allowed_references") or {}
        return VideoModelInfo(
            key=key, display_name=m.get("displayName", key),
            min_duration=int(dur.get("min", 1)), max_duration=int(dur.get("max", 10)),
            duration_step=dur.get("step"),
            resolutions=list(v.get("resolutions") or []),
            aspect_ratios=list(v.get("aspectRatios") or []),
            native_audio=bool(v.get("allowAudio")), always_audio=bool(v.get("alwaysAudio")),
            supports_reference=bool(v.get("supportsReference")),
            supports_text_to_video=bool(v.get("supportsTextToVideo")),
            max_reference_images=refs.get("images"), active=bool(m.get("active")),
            submit_mode=v.get("submitMode"))

    def image_api_mode(self, name: str | None, tier: str = "1k") -> str | None:
        """Map a UI resolution tier (1k|hd|4k) to the model's API `mode` value."""
        m = self.get(name)
        if not m:
            return None
        modes = (m.get("frontend") or {}).get("resolutionModes") or {}
        return modes.get(tier)

    # ---------------------------------------------------------- pricing
    def price_image(self, name: str | None, tier: str | None = None, capability: str = "generation") -> float:
        m = self.get(name)
        if not m:
            return 0.0
        cap = m.get("capabilities", {}).get(capability) or m.get("capabilities", {}).get("generation") or {}
        p = cap.get("pricing") or {}
        if "_flat" in p:
            return float(p["_flat"])
        tier = tier or cap.get("defaultMode") or "1k"
        return float(p.get(tier) or p.get("1k") or next(iter(p.values()), 0))

    def price_video(self, name: str, duration: float, resolution: str | None = None,
                    with_audio: bool = False, high_quality: bool = False) -> float:
        m = self.get(name)
        if not m:
            return 0.0
        v = m["capabilities"].get("video", {})
        p = v.get("pricing") or {}
        if "_flat" in p:
            base = float(p["_flat"])
            if with_audio and "_withAudio" in p:
                base = float(p["_withAudio"])
        else:
            rate = p.get(f"_perSecond{resolution}") if resolution else None
            base = float(rate if rate is not None else p.get("_perSecond", 0)) * float(duration)
        if with_audio and not v.get("alwaysAudio") and "_withAudio" not in p:
            base *= float(p.get("_audioMultiplier", 1))
        if high_quality:
            base *= float(p.get("_hqMultiplier", 1))
        return base

    def price_speech(self, name: str, characters: int, seconds: float | None = None) -> float:
        m = self.get(name)
        if not m:
            return 0.0
        p = (m["capabilities"].get("audio") or {}).get("pricing") or {}
        if "_per1kChars" in p:
            return float(p["_per1kChars"]) * max(1.0, math.ceil(characters / 100) / 10)
        if "_perSecond" in p:
            return float(p["_perSecond"]) * float(seconds or max(1, characters / 15))
        return 0.0

    def speech_voices(self, name: str) -> dict[str, str]:
        m = self.get(name) or {}
        return dict((m.get("capabilities", {}).get("audio") or {}).get("voices") or {})


def load_snapshot() -> Catalog:
    return Catalog(json.loads(SNAPSHOT.read_text()))


class CatalogCache:
    """Caches the live catalogue; falls back to the snapshot on any error."""

    def __init__(self, fetch: Callable[[], dict[str, Any]] | None, ttl: int = 3600):
        self.fetch = fetch
        self.ttl = ttl
        self._cat: Catalog | None = None
        self._at = 0.0
        self.source = "snapshot"

    def get(self) -> Catalog:
        if self._cat and time.time() - self._at < self.ttl:
            return self._cat
        if self.fetch:
            try:
                data = self.fetch()
                if isinstance(data, dict) and data.get("models"):
                    self._cat, self._at, self.source = Catalog(data), time.time(), "live"
                    return self._cat
            except Exception:  # noqa: BLE001 - fall back to snapshot
                pass
        if self._cat is None:
            self._cat = load_snapshot()
            self.source = "snapshot"
        self._at = time.time()
        return self._cat
