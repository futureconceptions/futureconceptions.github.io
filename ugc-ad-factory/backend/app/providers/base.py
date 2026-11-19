"""Provider interfaces. Every external AI service sits behind one of these so it
can be swapped (LetzAI, mocks, future vendors) without touching agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

MediaKind = Literal["image", "image_edit", "video", "speech", "music"]
JobState = Literal["running", "succeeded", "failed"]


class ProviderError(RuntimeError):
    """Raised for provider failures. `retryable` tells the job runner whether a
    resubmission can help (rate limits, 5xx, timeouts) or not (validation,
    content policy)."""

    def __init__(self, message: str, *, retryable: bool = False, status_code: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


# Callback that persists one provider HTTP call (ProviderRequest row).
RequestLogger = Callable[..., None]


def null_logger(**_: Any) -> None:
    return None


@dataclass
class MediaRequest:
    kind: MediaKind
    prompt: str = ""
    model: str | None = None
    width: int | None = None
    height: int | None = None
    image_urls: list[str] = field(default_factory=list)  # first frame / references
    last_frame_url: str | None = None
    duration: int | None = None
    resolution: str | None = None
    aspect_ratio: str | None = "9:16"
    with_audio: bool = False
    text: str | None = None  # speech
    voice: str | None = None
    language: str | None = None
    webhook_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v not in (None, [], {})}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MediaRequest":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SubmitResult:
    provider_job_id: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PollResult:
    state: JobState
    progress: int = 0
    output_url: str | None = None
    error: str | None = None
    credits: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoModelInfo:
    key: str
    display_name: str
    min_duration: int
    max_duration: int
    resolutions: list[str]
    aspect_ratios: list[str]
    native_audio: bool
    always_audio: bool
    supports_reference: bool
    supports_text_to_video: bool
    max_reference_images: int | None
    active: bool
    duration_step: int | None = None
    submit_mode: str | None = None


@runtime_checkable
class MediaProvider(Protocol):
    name: str

    def submit(self, req: MediaRequest, *, log: RequestLogger = null_logger) -> SubmitResult: ...

    def poll(self, kind: MediaKind, provider_job_id: str, *,
             log: RequestLogger = null_logger) -> PollResult: ...

    def download(self, url: str, dest_path: str) -> str: ...

    def upload_asset(self, path: str, mime_type: str, *,
                     log: RequestLogger = null_logger) -> str: ...

    def estimate_credits(self, req: MediaRequest) -> float: ...

    def video_model(self, model: str | None) -> VideoModelInfo: ...

    def list_models(self) -> dict[str, Any]: ...


@dataclass
class LipSyncResult:
    state: JobState
    output_url: str | None = None
    error: str | None = None
    provider_job_id: str | None = None


class LipSyncProvider(Protocol):
    name: str

    def available(self) -> bool: ...

    def submit(self, video_path: str, audio_path: str, *, log: RequestLogger = null_logger) -> str: ...

    def poll(self, provider_job_id: str, *, log: RequestLogger = null_logger) -> LipSyncResult: ...

    def download(self, url: str, dest_path: str) -> str: ...


T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    cost_usd: float = 0.0


@dataclass
class ImageInput:
    data: bytes
    media_type: str = "image/jpeg"
    label: str = ""


class LLMProvider(Protocol):
    name: str

    def structured(self, *, system: str, prompt: str, schema: type[T],
                   images: list[ImageInput] | None = None, task: str = "") -> tuple[T, LLMUsage]: ...

    @property
    def supports_vision(self) -> bool: ...


class TranscriptionProvider(Protocol):
    name: str

    def available(self) -> bool: ...

    def transcribe(self, audio_path: str, language: str | None = None) -> str: ...
