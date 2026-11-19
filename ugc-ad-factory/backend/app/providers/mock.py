"""Offline providers for development and tests. They produce real media files
with FFmpeg (so assembly and QA run for real) but never call paid APIs.
Jobs report `running` on the first poll and finish on the second, which
exercises the asynchronous polling path. State lives on disk so the API
process and Celery workers share it."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.media import ffmpeg as ff
from app.providers.base import (LipSyncResult, MediaKind, MediaRequest, PollResult, ProviderError,
                                RequestLogger, SubmitResult, VideoModelInfo, null_logger)
from app.providers.letzai.adapter import clamp_duration, estimate_with_catalog
from app.providers.letzai.catalog import load_snapshot


def _mock_root() -> Path:
    root = Path(os.environ.get("UGC_MOCK_DIR") or Path(get_settings().local_storage_dir).parent / "mock-provider")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _color(seed: str) -> str:
    h = hashlib.sha256(seed.encode()).hexdigest()
    return "0x" + h[:6]


class MockMediaProvider:
    name = "mock"

    def __init__(self, fail_prompts_containing: str | None = None):
        self.root = _mock_root()
        self.catalog = load_snapshot()
        self.fail_marker = fail_prompts_containing or os.environ.get("UGC_MOCK_FAIL_MARKER")

    def _path(self, name: str) -> Path:
        return self.root / name

    def _resolve(self, url: str) -> str:
        if not url.startswith("mock://"):
            raise ProviderError(f"mock provider cannot read {url}")
        p = self._path(url[len("mock://"):])
        if not p.exists():
            raise ProviderError(f"mock asset missing: {url}")
        return str(p)

    def submit(self, req: MediaRequest, *, log: RequestLogger = null_logger) -> SubmitResult:
        jid = uuid.uuid4().hex
        log(operation=f"mock_submit_{req.kind}", method="POST", endpoint=f"mock://{req.kind}",
            status_code=201, duration_ms=1, request={"prompt": req.prompt[:200]}, response={"id": jid})
        fail = bool(self.fail_marker and self.fail_marker in (req.prompt or ""))
        out = None
        meta: dict[str, Any] = {}
        if not fail:
            if req.kind in ("image", "image_edit"):
                out = f"{jid}.png"
                ff.make_still(str(self._path(out)), 720, 1280, color=_color(req.prompt[:80]))
            elif req.kind == "video":
                info = self.video_model(req.model)
                dur = clamp_duration(req.duration or info.min_duration, info)
                src = self._resolve(req.image_urls[0]) if req.image_urls else None
                if src is None:
                    src = str(self._path(f"{jid}_seed.png"))
                    ff.make_still(src, 720, 1280, color=_color(req.prompt[:80]))
                out = f"{jid}.mp4"
                # 'native audio' mock: a tone shaped like speech during the dialogue window
                tone = 180 + int(hashlib.md5(req.prompt.encode()).hexdigest()[:2], 16) if (
                    req.with_audio and info.native_audio) else None
                ff.make_clip_from_image(src, str(self._path(out)), dur, tone_hz=tone)
                meta["durationSeconds"] = dur
            elif req.kind == "music":
                out = f"{jid}.wav"
                ff.make_tone(str(self._path(out)), float(req.duration or 30), hz=110)
            elif req.kind == "speech":
                text = req.text or req.prompt
                dur = max(1.0, len(text.split()) / 2.5)
                out = f"{jid}.wav"
                ff.make_tone(str(self._path(out)), dur, hz=200 + (len(text) % 60))
                meta["durationSeconds"] = dur
        state = {"kind": req.kind, "polls": 0, "output": out, "fail": fail, "meta": meta,
                 "credits": self.estimate_credits(req)}
        self._path(f"{jid}.json").write_text(json.dumps(state))
        return SubmitResult(provider_job_id=jid, raw={"status": "new"})

    def poll(self, kind: MediaKind, provider_job_id: str, *, log: RequestLogger = null_logger) -> PollResult:
        p = self._path(f"{provider_job_id}.json")
        if not p.exists():
            raise ProviderError("unknown mock job")
        st = json.loads(p.read_text())
        st["polls"] += 1
        p.write_text(json.dumps(st))
        log(operation=f"mock_get_{kind}", method="GET", endpoint=f"mock://{kind}/{provider_job_id}",
            status_code=200, duration_ms=1, request=None, response={"polls": st["polls"]})
        if st["polls"] < 2:
            return PollResult(state="running", progress=50)
        if st["fail"]:
            return PollResult(state="failed", error="mock: generation failed (fail marker)")
        return PollResult(state="succeeded", progress=100, output_url=f"mock://{st['output']}",
                          credits=st["credits"], meta=st["meta"])

    def download(self, url: str, dest_path: str) -> str:
        shutil.copyfile(self._resolve(url), dest_path)
        return dest_path

    def upload_asset(self, path: str, mime_type: str, *, log: RequestLogger = null_logger) -> str:
        name = f"upload_{uuid.uuid4().hex}{os.path.splitext(path)[1] or '.bin'}"
        shutil.copyfile(path, self._path(name))
        log(operation="mock_upload", method="POST", endpoint="mock://user-assets", status_code=201,
            duration_ms=1, request={"mime": mime_type}, response={"name": name})
        return f"mock://{name}"

    def estimate_credits(self, req: MediaRequest) -> float:
        return estimate_with_catalog(self.catalog, req)

    def video_model(self, model: str | None) -> VideoModelInfo:
        return self.catalog.video_model(model or get_settings().letzai_video_model)

    def list_models(self) -> dict[str, Any]:
        c = self.catalog
        return {"source": "snapshot (mock mode)", "version": c.version, "image": c.list("generation"),
                "image_edit": c.list("editing"), "video": c.list("video"), "audio": c.list("audio")}


class MockLipSyncProvider:
    """Pretends to lip-sync by muxing the audio onto the video."""
    name = "mock"

    def __init__(self):
        self.root = _mock_root()

    def available(self) -> bool:
        return True

    def submit(self, video_path: str, audio_path: str, *, log: RequestLogger = null_logger) -> str:
        jid = uuid.uuid4().hex
        ff.mux_audio(video_path, audio_path, str(self.root / f"ls_{jid}.mp4"))
        log(operation="mock_lipsync_submit", method="POST", endpoint="mock://lipsync", status_code=200,
            duration_ms=1, request=None, response={"id": jid})
        return jid

    def poll(self, provider_job_id: str, *, log: RequestLogger = null_logger) -> LipSyncResult:
        return LipSyncResult(state="succeeded", output_url=f"mock://ls_{provider_job_id}.mp4",
                             provider_job_id=provider_job_id)

    def download(self, url: str, dest_path: str) -> str:
        shutil.copyfile(self.root / url[len("mock://"):], dest_path)
        return dest_path
