"""LetzAI implementation of MediaProvider.

Capability mapping (verified against the public API docs, 2026-11-19):
  text-to-image ........ POST /images (no image input on this route)
  image-to-image/ref ... POST /image-edits mode=context, inputImageUrls (max 9)
  text-to-video ........ POST /videos without image input
  image-to-video ....... POST /videos imageUrl (+ secondFrameUrl for last frame)
  reference assets ..... POST /videos assetUrls (model dependent)
  speech ............... POST /audios kind=speech
  uploads .............. POST /user-assets + presigned PUT
  status ............... GET /images|/image-edits|/videos|/audios/{id}
There is no public lip-sync endpoint and no video interruption endpoint.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import (MediaKind, MediaRequest, PollResult, ProviderError, RequestLogger,
                                SubmitResult, VideoModelInfo, null_logger)
from app.providers.letzai import schemas as S
from app.providers.letzai.catalog import CatalogCache
from app.providers.letzai.client import LetzAIClient
from app.services.safe_fetch import validate_url

MAX_DOWNLOAD_BYTES = 1_000_000_000

_EXT_BY_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "video/mp4": "mp4",
                "audio/mpeg": "mp3", "audio/wav": "wav", "audio/x-wav": "wav", "video/webm": "webm"}


def size_for(resolution: str | None, aspect: str | None = "9:16") -> tuple[int, int]:
    """Pixel size for a resolution tier; portrait for 9:16."""
    short = {"360p": 360, "480p": 480, "720p": 720, "768p": 768, "1080p": 1080,
             "2K": 1440, "4k": 2160}.get(resolution or "720p", 720)
    long_ = int(round(short * 16 / 9 / 2) * 2)
    if aspect in ("16:9", "21:9"):
        return long_, short
    if aspect == "1:1":
        return short, short
    return short, long_


class LetzAIProvider:
    name = "letzai"

    def __init__(self, client: LetzAIClient | None = None):
        s = get_settings()
        if client is None:
            if not s.letzai_api_key:
                raise ProviderError("LETZAI_API_KEY is not configured")
            client = LetzAIClient(s.letzai_api_key.get_secret_value(), s.letzai_base_url)
        self.client = client
        self.org = s.letzai_organization_id
        self.catalog = CatalogCache(self.client.get_catalog, ttl=s.letzai_catalog_ttl_seconds)

    # ------------------------------------------------------------ submit
    def submit(self, req: MediaRequest, *, log: RequestLogger = null_logger) -> SubmitResult:
        s = get_settings()
        if req.kind == "image" and req.image_urls:
            req = MediaRequest(**{**req.__dict__, "kind": "image_edit"})  # POST /images has no image input
        if req.kind == "image":
            model = req.model or s.letzai_image_model
            w, h = req.width or 1080, req.height or 1920
            body = S.ImageCreateRequest(
                prompt=req.prompt, width=max(480, min(2160, w)), height=max(480, min(2160, h)),
                quality=int(req.extra.get("quality", 2)), creativity=int(req.extra.get("creativity", 2)),
                hasWatermark=s.letzai_has_watermark, baseModel=model,
                mode=req.extra.get("mode") or self.catalog.get().image_api_mode(model, req.extra.get("tier", "1k")),
                webhookUrl=req.webhook_url, organizationId=self.org)
            r = self.client.create_image(body, log=log)
        elif req.kind == "image_edit":
            model = req.model or s.letzai_edit_model
            ar = req.aspect_ratio if req.aspect_ratio in ("1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21") else None
            body = S.ImageEditRequest(
                mode="context", prompt=req.prompt, inputImageUrls=req.image_urls[:9], baseModel=model,
                settings=S.ImageEditSettings(resolution="2k", aspect_ratio=ar, model=model),
                webhookUrl=req.webhook_url, organizationId=self.org, hidePrompt=True)
            r = self.client.create_image_edit(body, log=log)
        elif req.kind == "video":
            info = self.video_model(req.model or s.letzai_video_model)
            duration = clamp_duration(req.duration or info.min_duration, info)
            resolution = req.resolution if req.resolution in info.resolutions else (
                info.resolutions[0] if info.resolutions else None)
            w, h = size_for(resolution, req.aspect_ratio)
            first = req.image_urls[0] if req.image_urls else None
            refs = req.image_urls[1:] if info.supports_reference else []
            if info.max_reference_images is not None:
                refs = refs[: info.max_reference_images]
            if not first and not info.supports_text_to_video:
                raise ProviderError(f"{info.key} does not support text-to-video; an image is required")
            settings = S.VideoSettings(
                mode=info.submit_mode or info.key, duration=duration, resolution=resolution,
                withSound=(True if info.always_audio else (req.with_audio if info.native_audio else None)))
            body = S.VideoCreateRequest(
                prompt=req.prompt, imageUrl=first, secondFrameUrl=req.last_frame_url,
                assetUrls=refs or None, width=w, height=h, settings=settings,
                webhookUrl=req.webhook_url, organizationId=self.org, hidePrompt=True)
            r = self.client.create_video(body, log=log)
        elif req.kind == "speech":
            model = req.model or s.letzai_speech_model
            body = S.AudioCreateRequest(
                kind="speech", baseModel=model, text=req.text or req.prompt,
                prompt=(req.extra.get("direction") or None),
                settings=S.AudioSettings(voice=req.voice, language=req.language),
                webhookUrl=req.webhook_url, organizationId=self.org, hidePrompt=True)
            r = self.client.create_audio(body, log=log)
        elif req.kind == "music":
            body = S.AudioCreateRequest(
                kind="music", baseModel=req.model or "audio-eleven-music", prompt=req.prompt[:2000],
                settings=S.AudioSettings(durationSeconds=req.duration, instrumental=True),
                webhookUrl=req.webhook_url, organizationId=self.org, hidePrompt=True)
            r = self.client.create_audio(body, log=log)
        else:  # pragma: no cover
            raise ProviderError(f"unsupported kind {req.kind}")
        return SubmitResult(provider_job_id=r.id, raw={"status": r.status})

    # ------------------------------------------------------------ poll
    def poll(self, kind: MediaKind, provider_job_id: str, *, log: RequestLogger = null_logger) -> PollResult:
        if kind == "image":
            r = self.client.get_image(provider_job_id, log=log)
            return _normalize(r.status, r.progress, r.original_url(), r.statusDetail, S.IMAGE_SUCCESS,
                              hidden_ok=True)
        if kind == "image_edit":
            r = self.client.get_image_edit(provider_job_id, log=log)
            return _normalize(r.status, r.progress, r.original_url(), r.statusDetail, S.EDIT_SUCCESS)
        if kind == "video":
            r = self.client.get_video(provider_job_id, log=log)
            res = _normalize(r.status, r.progress, r.original_url(), r.statusDetail, S.VIDEO_SUCCESS)
            res.meta = {"durationSeconds": r.durationSeconds, "width": r.width, "height": r.height}
            return res
        if kind in ("speech", "music"):
            r = self.client.get_audio(provider_job_id, log=log)
            res = _normalize(r.status, r.progress, r.audioUrl, r.statusDetail, S.AUDIO_SUCCESS)
            res.credits = r.credits
            res.meta = {"durationSeconds": r.durationSeconds}
            return res
        raise ProviderError(f"unsupported kind {kind}")

    # ------------------------------------------------------------ assets
    def download(self, url: str, dest_path: str) -> str:
        validate_url(url)
        size = 0
        with httpx.Client(timeout=300, follow_redirects=True) as c, c.stream("GET", url) as r:
            if r.status_code >= 400:
                raise ProviderError(f"download failed: HTTP {r.status_code}", retryable=r.status_code >= 500)
            with open(dest_path, "wb") as f:
                for chunk in r.iter_bytes(1 << 20):
                    size += len(chunk)
                    if size > MAX_DOWNLOAD_BYTES:
                        raise ProviderError("download exceeds size limit")
                    f.write(chunk)
        return dest_path

    def upload_asset(self, path: str, mime_type: str, *, log: RequestLogger = null_logger) -> str:
        ext = _EXT_BY_MIME.get(mime_type) or os.path.splitext(path)[1].lstrip(".") or "jpg"
        with open(path, "rb") as f:
            data = f.read()
        return self.client.upload_file(data, ext, mime_type, os.path.basename(path), log=log).imageUrl

    # ------------------------------------------------------------ models & cost
    def video_model(self, model: str | None) -> VideoModelInfo:
        return self.catalog.get().video_model(model or get_settings().letzai_video_model)

    def list_models(self) -> dict[str, Any]:
        cat = self.catalog.get()
        return {"source": self.catalog.source, "version": cat.version,
                "image": cat.list("generation"), "image_edit": cat.list("editing"),
                "video": cat.list("video"), "audio": cat.list("audio")}

    def estimate_credits(self, req: MediaRequest) -> float:
        return estimate_with_catalog(self.catalog.get(), req)

    def quote(self, req: MediaRequest) -> float:
        """Server-side estimate via POST /generations/quote (nothing is charged)."""
        s = get_settings()
        if req.kind == "video":
            info = self.video_model(req.model)
            q = S.QuoteRequest(type="video", baseModel=info.key, duration=req.duration,
                               resolution=req.resolution, withSound=req.with_audio,
                               organizationId=self.org)
        elif req.kind == "speech":
            q = S.QuoteRequest(type="audio", baseModel=req.model or s.letzai_speech_model,
                               characters=len(req.text or ""), organizationId=self.org)
        else:
            q = S.QuoteRequest(type="image" if req.kind == "image" else "image-edit",
                               baseModel=req.model or s.letzai_image_model, organizationId=self.org)
        return float(self.client.quote(q).credits)


def clamp_duration(d: float, info: VideoModelInfo) -> int:
    d = int(round(d))
    d = max(info.min_duration, min(info.max_duration, d))
    if info.duration_step and info.duration_step > 1:
        step = info.duration_step
        d = max(info.min_duration, min(info.max_duration, int(round(d / step) * step)))
    return d


def estimate_with_catalog(cat, req: MediaRequest) -> float:
    s = get_settings()
    if req.kind == "image":
        return cat.price_image(req.model or s.letzai_image_model, req.extra.get("tier"))
    if req.kind == "image_edit":
        return cat.price_image(req.model or s.letzai_edit_model, req.extra.get("tier"), "editing")
    if req.kind == "video":
        info = cat.video_model(req.model or s.letzai_video_model)
        return cat.price_video(info.key, clamp_duration(req.duration or info.min_duration, info),
                               req.resolution, req.with_audio)
    if req.kind == "speech":
        return cat.price_speech(req.model or s.letzai_speech_model, len(req.text or ""))
    if req.kind == "music":
        m = cat.get(req.model or "audio-eleven-music") or {}
        rate = ((m.get("capabilities", {}).get("audio") or {}).get("pricing") or {}).get("_perSecond", 0)
        return float(rate) * float(req.duration or 30)
    return 0.0


def _normalize(status: str, progress, url: str | None, detail: str | None, success: set[str],
               hidden_ok: bool = False) -> PollResult:
    st = (status or "").lower()
    if st in success or (hidden_ok and st == "hidden" and url):
        if not url:
            # Terminal status but no asset: never assume success.
            return PollResult(state="failed", error=f"status {st} but no output URL")
        return PollResult(state="succeeded", progress=100, output_url=url)
    if st in S.FAILURE:
        return PollResult(state="failed", progress=int(progress or 0),
                          error=detail or f"generation {st}")
    return PollResult(state="running", progress=int(progress or 0))
