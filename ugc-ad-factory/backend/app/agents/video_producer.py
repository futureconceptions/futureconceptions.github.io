"""Agent 5 - Video Producer: builds LetzAI video requests for scenes.

Image-to-video from a per-scene keyframe (which itself was derived from the
creator anchor + real product photo) is the default, because identity and
product appearance matter. Text-to-video is used only when no keyframe exists
and the model supports it."""
from __future__ import annotations

import math

from app.providers.base import MediaRequest, VideoModelInfo


def video_request(*, prompt: str, duration: float, info: VideoModelInfo, keyframe_url: str | None,
                  reference_urls: list[str], resolution: str, native_audio: bool) -> MediaRequest:
    dur = max(info.min_duration, min(info.max_duration, int(math.ceil(duration))))
    images = [keyframe_url] if keyframe_url else []
    if info.supports_reference and keyframe_url:
        images += reference_urls
    return MediaRequest(kind="video", prompt=prompt, model=info.key, duration=dur,
                        resolution=resolution if resolution in info.resolutions else None,
                        aspect_ratio="9:16", image_urls=images,
                        with_audio=bool(native_audio and info.native_audio))


def keyframe_request(*, prompt: str, anchor_url: str, product_url: str | None, model: str | None) -> MediaRequest:
    urls = [anchor_url] + ([product_url] if product_url else [])
    return MediaRequest(kind="image_edit", prompt=prompt, model=model, image_urls=urls, aspect_ratio="9:16")


def anchor_request(*, prompt: str, model: str | None) -> MediaRequest:
    return MediaRequest(kind="image", prompt=prompt, model=model, width=1080, height=1920)
