"""Typed LetzAI request/response models.

Derived from the public OpenAPI spec (https://api.letz.ai/doc-yaml) and
https://letz.ai/systemprompts/api_instructions.md (inspected 2026-11-19).

Request models use extra="forbid" because the API validates request bodies
strictly and returns 400 for unknown fields. Response models use
extra="allow" and only type the fields we rely on.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class _Req(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def body(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, by_alias=True)


class _Resp(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ---------------------------------------------------------------- statuses
IMAGE_SUCCESS = {"ready"}
VIDEO_SUCCESS = {"ready", "saved"}
EDIT_SUCCESS = {"ready", "saved"}
AUDIO_SUCCESS = {"ready"}
FAILURE = {"failed", "interrupted", "not_allowed"}
IN_FLIGHT = {"new", "generating", "pending"}


# ---------------------------------------------------------------- images
class ImageCreateRequest(_Req):
    prompt: str = Field(min_length=1, max_length=8000)
    width: int = Field(default=1600, ge=480, le=2160)
    height: int = Field(default=1600, ge=480, le=2160)
    quality: int = Field(default=2, ge=1, le=6)
    creativity: int = Field(default=2, ge=1, le=6)
    hasWatermark: bool = True
    systemVersion: Literal[2, 3] | None = None
    mode: str | None = Field(default=None, max_length=32)  # resolution tier, model-specific
    hideFromUserProfile: bool = True
    baseModel: str | None = Field(default=None, max_length=255)
    webhookUrl: str | None = None
    organizationId: str | None = None


class ImageResponse(_Resp):
    id: str
    status: str
    statusDetail: str | None = None
    progress: int | float | None = 0
    imageVersions: dict[str, str] | None = None
    baseModel: str | None = None

    def original_url(self) -> str | None:
        return (self.imageVersions or {}).get("original")


# ---------------------------------------------------------------- image edits
AspectRatio = Literal["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"]


class ImageEditSettings(_Req):
    resolution: Literal["2k", "4k"] = "2k"
    aspect_ratio: AspectRatio | None = None
    model: str | None = None


class ImageEditRequest(_Req):
    mode: Literal["context", "skin"] = "context"
    prompt: str | None = Field(default=None, max_length=8000)
    inputImageUrls: list[str] | None = Field(default=None, max_length=9)
    imageUrl: str | None = None
    originalImageCompletionId: str | None = None
    imageCompletionsCount: int = Field(default=1, ge=1, le=5)
    baseModel: str | None = None
    settings: ImageEditSettings | None = None
    webhookUrl: str | None = None
    organizationId: str | None = None
    hidePrompt: bool | None = None

    @field_validator("inputImageUrls")
    @classmethod
    def _non_empty(cls, v):
        if v is not None and len(v) == 0:
            return None
        return v


class _ImageCompletion(_Resp):
    id: str | None = None
    imageVersions: dict[str, str] | None = None


class ImageEditResponse(_Resp):
    id: str
    status: str
    statusDetail: str | None = None
    progress: int | float | None = 0
    generatedImageCompletion: _ImageCompletion | None = None
    imageCompletionChoices: list[_ImageCompletion] | None = None

    def original_url(self) -> str | None:
        if self.generatedImageCompletion and self.generatedImageCompletion.imageVersions:
            return self.generatedImageCompletion.imageVersions.get("original")
        for c in self.imageCompletionChoices or []:
            if c.imageVersions and c.imageVersions.get("original"):
                return c.imageVersions["original"]
        return None


# ---------------------------------------------------------------- videos
class VideoSettings(BaseModel):
    # `settings` is a free-form object on the API; we type the documented keys.
    model_config = ConfigDict(extra="allow")
    mode: str
    duration: int | None = Field(default=None, ge=1, le=60)
    withSound: bool | None = None
    highQuality: bool | None = None
    resolution: Literal["360p", "480p", "720p", "768p", "1080p", "2K", "4k"] | None = None


class VideoCreateRequest(_Req):
    prompt: str = Field(min_length=1, max_length=8000)
    originalImageCompletionId: str | None = None
    imageUrl: str | None = None
    imageUrls: list[str] | None = None
    secondFrameUrl: str | None = None
    assetUrls: list[str] | None = None
    width: int | None = None
    height: int | None = None
    baseModel: str | None = Field(default=None, max_length=255)
    settings: VideoSettings
    webhookUrl: str | None = None
    organizationId: str | None = None
    hidePrompt: bool | None = None

    def body(self) -> dict[str, Any]:
        b = super().body()
        b["settings"] = self.settings.model_dump(exclude_none=True)
        return b


class VideoResponse(_Resp):
    id: str
    status: str
    statusDetail: str | None = None
    progress: int | float | None = 0
    videoVersions: dict[str, str] | None = None
    durationSeconds: float | None = None
    width: int | None = None
    height: int | None = None

    def original_url(self) -> str | None:
        return (self.videoVersions or {}).get("original")


# ---------------------------------------------------------------- audio
class AudioSettings(_Req):
    voice: str | None = None
    language: str | None = None
    durationSeconds: int | None = Field(default=None, ge=1, le=600)
    instrumental: bool | None = None


class AudioCreateRequest(_Req):
    kind: Literal["speech", "music", "sound_effect"]
    baseModel: str
    prompt: str | None = Field(default=None, max_length=2000)
    text: str | None = Field(default=None, max_length=10000)
    settings: AudioSettings | None = None
    organizationId: str | None = None
    webhookUrl: str | None = None
    hidePrompt: bool | None = None

    @model_validator(mode="after")
    def _speech_needs_text(self):
        if self.kind == "speech" and not self.text:
            raise ValueError("speech requires text")
        if self.kind in ("music", "sound_effect") and not self.prompt:
            raise ValueError(f"{self.kind} requires a prompt")
        return self


class AudioResponse(_Resp):
    id: str
    kind: str | None = None
    status: str
    statusDetail: str | None = None
    progress: int | float | None = 0
    audioUrl: str | None = None
    durationSeconds: float | None = None
    credits: float | None = None


# ---------------------------------------------------------------- uploads
UploadExtension = Literal["jpg", "jpeg", "png", "gif", "webp", "mp4", "webm", "mov", "avi",
                          "mp3", "wav", "ogg", "m4a", "aac", "flac"]


class UserAssetCreateRequest(_Req):
    extension: UploadExtension
    numberOfImages: int = 1
    originalFilename: str | None = None
    mimeType: str | None = None
    fileSize: int | None = None
    caption: str | None = None
    metadata: dict[str, Any] | None = None


class UserAssetResponse(_Resp):
    id: str
    imageUrl: str
    uploadUrl: str | None = None


# ---------------------------------------------------------------- quote
class QuoteRequest(_Req):
    type: Literal["image", "image-edit", "video", "video-edit", "upscale", "audio"]
    baseModel: str
    mode: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    withSound: bool | None = None
    quantity: int | None = Field(default=None, ge=1, le=100)
    characters: int | None = None
    resolution: str | None = None
    organizationId: str | None = None


class QuoteResponse(_Resp):
    credits: float
    estimate: bool = True
    breakdown: dict[str, Any] | None = None


__all__ = [n for n in dir() if not n.startswith("_") and n != "annotations"]
_ = HttpUrl  # re-exported for callers that validate URLs
