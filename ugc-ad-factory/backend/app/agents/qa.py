"""Agent 9 - Quality Assurance.

Deterministic technical checks (FFprobe/FFmpeg) plus multimodal inspection
when a vision-capable LLM is configured, and transcript comparison when a
transcription provider is configured. Checks that could not run are reported
as `not_checked` - never as passed. Automated QA cannot guarantee realism.

Thresholds follow the reference referee: identity_match AND score >= 0.80;
transcript similarity >= 0.86 counts as a dialogue match.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

from app.agents import prompts as P
from app.agents.schemas import SceneVisualQA
from app.media import ffmpeg as ff
from app.providers.base import ImageInput, LLMUsage
from app.providers.transcription import dialogue_similarity

REGENERABLE = {"identity", "product_accuracy", "invented_branding", "visual_artifacts", "hand_anatomy",
               "dialogue_accuracy", "decode", "video_stream"}
BLOCKING = {"high", "critical"}


@dataclass
class QAResult:
    passed: bool
    score: float | None
    checks: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    usage: LLMUsage | None = None

    @property
    def regenerable(self) -> bool:
        return any(i["check"] in REGENERABLE and i["severity"] in BLOCKING for i in self.issues)


def _check(checks, issues, name, status, detail="", severity=None, value=None):
    checks.append({"check": name, "status": status, "detail": detail, "value": value})
    if status == "failed" and severity:
        issues.append({"check": name, "severity": severity, "detail": detail})


class QualityAssurance:
    def __init__(self, llm, transcriber, min_identity: float = 0.80, dialogue_threshold: float = 0.86):
        self.llm = llm
        self.transcriber = transcriber
        self.min_identity = min_identity
        self.dialogue_threshold = dialogue_threshold

    # ------------------------------------------------------------ scenes
    def check_scene(self, *, clip: str, dialogue: str, language: str, audio_source: str | None,
                    lipsync_status: str | None, anchor_image: str | None, product_image: str | None,
                    expects_product: bool) -> QAResult:
        checks, issues = [], []
        try:
            info = ff.probe(clip)
        except ff.FFmpegError as e:
            _check(checks, issues, "decode", "failed", str(e), "critical")
            return QAResult(False, 0.0, checks, issues)
        _check(checks, issues, "video_stream", "passed" if info.has_video else "failed",
               f"{info.width}x{info.height} {info.vcodec}", "critical")
        short = min(info.width or 0, info.height or 0)
        _check(checks, issues, "resolution", "passed" if short >= 480 else "failed",
               f"short side {short}px", "medium", short)
        _check(checks, issues, "duration", "passed" if info.duration >= 1.0 else "failed",
               f"{info.duration:.2f}s", "high", info.duration)
        ok, err = ff.decode_ok(clip)
        _check(checks, issues, "decode", "passed" if ok else "failed", err, "high")
        if dialogue:
            if audio_source == "native":
                _check(checks, issues, "audio_present", "passed" if info.has_audio else "failed",
                       "native dialogue expected in clip", "high")
            if info.has_audio:
                st = ff.audio_stats(clip)
                clipped = st.max_volume_db is not None and st.max_volume_db >= -0.1
                _check(checks, issues, "audio_clipping", "failed" if clipped else "passed",
                       f"max volume {st.max_volume_db} dB", "medium", st.max_volume_db)
        # dialogue accuracy via transcription
        if dialogue and audio_source == "native" and info.has_audio:
            if self.transcriber.available():
                with tempfile.TemporaryDirectory() as td:
                    wav = ff.extract_audio(clip, os.path.join(td, "a.wav"), rate=16000, mono=True)
                    text = self.transcriber.transcribe(wav, language)
                sim = dialogue_similarity(dialogue, text)
                _check(checks, issues, "dialogue_accuracy", "passed" if sim >= self.dialogue_threshold else "failed",
                       f"similarity {sim:.2f}; heard: {text[:200]}", "high", round(sim, 3))
            else:
                _check(checks, issues, "dialogue_accuracy", "not_checked", "no transcription provider configured")
        # lip sync
        if dialogue:
            ls = {"native": ("not_checked", "model-native audio; sync assumed, not measured"),
                  "synced": ("passed", "external lip-sync applied"),
                  "voiceover": ("warning", "voice-over edit: mouth is not synced to speech")}.get(
                lipsync_status or "", ("not_checked", ""))
            _check(checks, issues, "lip_sync", ls[0], ls[1])
            if ls[0] == "warning":
                issues.append({"check": "lip_sync", "severity": "low", "detail": ls[1]})
        # multimodal inspection
        usage = None
        score = None
        if self.llm.supports_vision and anchor_image:
            frames = self._frames(clip, info.duration)
            images = [ImageInput(open(anchor_image, "rb").read(), _mime(anchor_image), "IDENTITY REFERENCE")]
            if product_image and expects_product:
                images.append(ImageInput(open(product_image, "rb").read(), _mime(product_image), "REAL PRODUCT"))
            images += [ImageInput(b, "image/jpeg", f"FRAME {i + 1}") for i, b in enumerate(frames)]
            vqa, usage = self.llm.structured(
                system=P.QA_SYSTEM, schema=SceneVisualQA, images=images, task="scene_qa",
                prompt=(f"Product expected in shot: {expects_product}. Evaluate the frames. "
                        "Report every problem as an issue with a severity."))
            score = vqa.overall_score
            id_ok = vqa.identity_match and vqa.identity_score >= self.min_identity
            _check(checks, issues, "identity", "passed" if id_ok else "failed",
                   f"identity_score={vqa.identity_score:.2f}", "high", vqa.identity_score)
            if expects_product and product_image:
                st = {"ok": "passed", "mismatch": "failed"}.get(vqa.product_accuracy, "not_checked")
                _check(checks, issues, "product_accuracy", st, vqa.product_accuracy, "high")
            _check(checks, issues, "invented_branding", "failed" if vqa.invented_branding else "passed",
                   "garbled or invented text/logos" if vqa.invented_branding else "", "high")
            _check(checks, issues, "hand_anatomy", "passed" if vqa.hand_anatomy_ok else "failed",
                   "", "medium")
            _check(checks, issues, "visual_artifacts", "failed" if vqa.visual_artifacts else "passed", "", "high")
            _check(checks, issues, "continuity", "passed" if vqa.continuity_ok else "failed", "", "medium")
            for i in vqa.issues:
                issues.append({"check": f"vision:{i.check}", "severity": i.severity, "detail": i.detail})
        else:
            for name in ("identity", "product_accuracy", "invented_branding", "hand_anatomy",
                         "visual_artifacts", "continuity"):
                _check(checks, issues, name, "not_checked", "no vision-capable QA model configured")
        passed = not any(i["severity"] in BLOCKING for i in issues)
        return QAResult(passed, score, checks, issues, usage)

    def _frames(self, clip: str, duration: float) -> list[bytes]:
        out = []
        with tempfile.TemporaryDirectory() as td:
            for i, f in enumerate((0.15, 0.5, 0.85)):
                p = os.path.join(td, f"f{i}.jpg")
                try:
                    ff.extract_frame(clip, duration * f, p, width=540)
                    out.append(open(p, "rb").read())
                except ff.FFmpegError:
                    continue
        return out

    # ------------------------------------------------------------ exports
    def check_export(self, path: str, *, target_duration: float, expect_w: int = ff.OUT_W,
                     expect_h: int = ff.OUT_H) -> QAResult:
        checks, issues = [], []
        try:
            info = ff.probe(path)
        except ff.FFmpegError as e:
            _check(checks, issues, "export_integrity", "failed", str(e), "critical")
            return QAResult(False, 0.0, checks, issues)
        _check(checks, issues, "resolution", "passed" if (info.width, info.height) == (expect_w, expect_h) else "failed",
               f"{info.width}x{info.height}", "high")
        _check(checks, issues, "video_codec", "passed" if info.vcodec == "h264" else "failed", info.vcodec or "", "high")
        _check(checks, issues, "audio_codec", "passed" if info.acodec == "aac" else "failed", info.acodec or "", "high")
        _check(checks, issues, "container", "passed" if "mp4" in (info.format_name or "") else "failed",
               info.format_name or "", "high")
        lo, hi = target_duration * 0.6, target_duration * 1.6 + 3
        _check(checks, issues, "duration", "passed" if lo <= info.duration <= hi else "failed",
               f"{info.duration:.1f}s (target {target_duration}s)", "medium", info.duration)
        ok, err = ff.decode_ok(path)
        _check(checks, issues, "export_integrity", "passed" if ok else "failed", err, "critical")
        st = ff.audio_stats(path)
        if st.integrated_lufs is not None:
            _check(checks, issues, "loudness", "passed" if -19 <= st.integrated_lufs <= -13 else "failed",
                   f"{st.integrated_lufs} LUFS (target -16)", "low", st.integrated_lufs)
        if st.max_volume_db is not None:
            _check(checks, issues, "audio_clipping", "passed" if st.max_volume_db < -0.1 else "failed",
                   f"max {st.max_volume_db} dB", "medium", st.max_volume_db)
        black = ff.black_segments(path)
        _check(checks, issues, "black_frames", "passed" if not black else "failed", str(black[:3]), "medium")
        frozen = [f for f in ff.frozen_segments(path, 2.5) if f[1] - f[0] >= 2.5]
        _check(checks, issues, "frozen_video", "passed" if not frozen else "failed", str(frozen[:3]), "low")
        passed = not any(i["severity"] in BLOCKING for i in issues)
        return QAResult(passed, None, checks, issues)


def _mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
