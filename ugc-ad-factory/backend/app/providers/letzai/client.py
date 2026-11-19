"""Low-level typed LetzAI REST client.

* Bearer authentication; the key never leaves the backend.
* Retries with exponential backoff (honouring Retry-After) on 429, 5xx and
  network errors. 4xx validation errors are not retried.
* Every call is reported to a RequestLogger so it lands in provider_requests.
"""
from __future__ import annotations

import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.providers.base import ProviderError, RequestLogger, null_logger
from app.providers.letzai import schemas as S

R = TypeVar("R", bound=BaseModel)

RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


def _excerpt(obj: Any, limit: int = 2000) -> Any:
    """Small, secret-free copy of a payload for the audit log."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k.lower() in ("authorization", "uploadurl", "previewimage"):
                out[k] = "[redacted]"
            else:
                out[k] = _excerpt(v, limit)
        return out
    if isinstance(obj, list):
        return [_excerpt(v, limit) for v in obj[:20]]
    if isinstance(obj, str) and len(obj) > limit:
        return obj[:limit] + "…"
    return obj


class LetzAIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.letz.ai", *,
                 timeout: float = 60.0, max_retries: int = 4, backoff_base: float = 1.0,
                 transport: httpx.BaseTransport | None = None, sleep=time.sleep):
        if not api_key:
            raise ValueError("LETZAI_API_KEY is required for the LetzAI client")
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout,
                                  transport=transport,
                                  headers={"Authorization": f"Bearer {api_key}",
                                           "Accept": "application/json",
                                           "User-Agent": "ugc-ad-factory/1.0"})
        self._upload_http = httpx.Client(timeout=300, transport=transport)
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep

    def close(self) -> None:
        self._http.close()
        self._upload_http.close()

    # ------------------------------------------------------------ core
    def request(self, method: str, path: str, *, json: dict | None = None,
                params: dict | None = None, operation: str = "",
                log: RequestLogger = null_logger) -> Any:
        attempt = 0
        while True:
            attempt += 1
            t0 = time.monotonic()
            try:
                resp = self._http.request(method, path, json=json, params=params)
            except httpx.TransportError as e:
                ms = int((time.monotonic() - t0) * 1000)
                log(operation=operation or path, method=method, endpoint=path, status_code=None,
                    duration_ms=ms, request=_excerpt(json), response=None, error=str(e))
                if attempt > self.max_retries:
                    raise ProviderError(f"LetzAI network error: {e}", retryable=True) from e
                self._sleep(self._backoff(attempt, None))
                continue
            ms = int((time.monotonic() - t0) * 1000)
            try:
                body: Any = resp.json() if resp.content else None
            except ValueError:
                body = {"raw": resp.text[:500]}
            ok = resp.status_code < 400
            log(operation=operation or path, method=method, endpoint=path,
                status_code=resp.status_code, duration_ms=ms, request=_excerpt(json),
                response=_excerpt(body), error=None if ok else _err_message(body, resp))
            if ok:
                return body
            retryable = resp.status_code in RETRY_STATUSES
            if retryable and attempt <= self.max_retries:
                self._sleep(self._backoff(attempt, resp.headers.get("retry-after")))
                continue
            raise ProviderError(f"LetzAI {method} {path} -> {resp.status_code}: "
                                f"{_err_message(body, resp)}",
                                retryable=retryable, status_code=resp.status_code)

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return min(60.0, float(retry_after))
            except ValueError:
                pass
        return min(60.0, self.backoff_base * (2 ** (attempt - 1)))

    def _typed(self, model: type[R], data: Any) -> R:
        try:
            return model.model_validate(data)
        except ValidationError as e:
            raise ProviderError(f"Unexpected LetzAI response shape for {model.__name__}: {e}") from e

    # ------------------------------------------------------------ images
    def create_image(self, req: S.ImageCreateRequest, log: RequestLogger = null_logger) -> S.ImageResponse:
        return self._typed(S.ImageResponse, self.request("POST", "/images", json=req.body(),
                                                         operation="create_image", log=log))

    def get_image(self, image_id: str, log: RequestLogger = null_logger) -> S.ImageResponse:
        return self._typed(S.ImageResponse, self.request("GET", f"/images/{image_id}",
                                                         operation="get_image", log=log))

    def interrupt_image(self, image_id: str, log: RequestLogger = null_logger) -> None:
        self.request("PUT", f"/images/{image_id}/interruption", operation="interrupt_image", log=log)

    # ------------------------------------------------------------ image edits
    def create_image_edit(self, req: S.ImageEditRequest, log: RequestLogger = null_logger) -> S.ImageEditResponse:
        if not (req.imageUrl or req.inputImageUrls or req.originalImageCompletionId):
            raise ValueError("image edit needs imageUrl, inputImageUrls or originalImageCompletionId")
        return self._typed(S.ImageEditResponse, self.request("POST", "/image-edits", json=req.body(),
                                                             operation="create_image_edit", log=log))

    def get_image_edit(self, edit_id: str, log: RequestLogger = null_logger) -> S.ImageEditResponse:
        return self._typed(S.ImageEditResponse, self.request("GET", f"/image-edits/{edit_id}",
                                                             operation="get_image_edit", log=log))

    # ------------------------------------------------------------ videos
    def create_video(self, req: S.VideoCreateRequest, log: RequestLogger = null_logger) -> S.VideoResponse:
        return self._typed(S.VideoResponse, self.request("POST", "/videos", json=req.body(),
                                                         operation="create_video", log=log))

    def get_video(self, video_id: str, log: RequestLogger = null_logger) -> S.VideoResponse:
        return self._typed(S.VideoResponse, self.request("GET", f"/videos/{video_id}",
                                                         operation="get_video", log=log))

    # ------------------------------------------------------------ audio
    def create_audio(self, req: S.AudioCreateRequest, log: RequestLogger = null_logger) -> S.AudioResponse:
        return self._typed(S.AudioResponse, self.request("POST", "/audios", json=req.body(),
                                                         operation="create_audio", log=log))

    def get_audio(self, audio_id: str, log: RequestLogger = null_logger) -> S.AudioResponse:
        return self._typed(S.AudioResponse, self.request("GET", f"/audios/{audio_id}",
                                                         operation="get_audio", log=log))

    # ------------------------------------------------------------ uploads
    def upload_file(self, data: bytes, extension: str, mime_type: str, filename: str | None = None,
                    log: RequestLogger = null_logger) -> S.UserAssetResponse:
        """Two-step upload: POST /user-assets, then PUT the bytes to the
        pre-signed uploadUrl WITHOUT the Authorization header."""
        req = S.UserAssetCreateRequest(extension=extension.lower().lstrip("."), mimeType=mime_type,
                                       fileSize=len(data), originalFilename=filename)
        asset = self._typed(S.UserAssetResponse, self.request("POST", "/user-assets", json=req.body(),
                                                              operation="create_user_asset", log=log))
        if not asset.uploadUrl:
            raise ProviderError("LetzAI did not return an uploadUrl")
        t0 = time.monotonic()
        put = self._upload_http.put(asset.uploadUrl, content=data, headers={"Content-Type": mime_type})
        log(operation="upload_put", method="PUT", endpoint="<presigned upload url>",
            status_code=put.status_code, duration_ms=int((time.monotonic() - t0) * 1000),
            request={"bytes": len(data), "contentType": mime_type}, response=None,
            error=None if put.status_code < 400 else put.text[:300])
        if put.status_code >= 400:
            raise ProviderError(f"upload PUT failed with {put.status_code}",
                                retryable=put.status_code >= 500)
        return asset

    # ------------------------------------------------------------ catalogue & quotes
    def get_catalog(self) -> dict[str, Any]:
        return self.request("GET", "/catalog", operation="get_catalog")

    def quote(self, req: S.QuoteRequest, log: RequestLogger = null_logger) -> S.QuoteResponse:
        return self._typed(S.QuoteResponse, self.request("POST", "/generations/quote", json=req.body(),
                                                         operation="quote", log=log))

    def list_models(self, params: dict | None = None) -> Any:
        return self.request("GET", "/models", params=params, operation="list_models")


def _err_message(body: Any, resp: httpx.Response) -> str:
    if isinstance(body, dict):
        msg = body.get("message") or body.get("error") or body.get("detail")
        if isinstance(msg, list):
            msg = "; ".join(map(str, msg))
        if msg:
            return str(msg)[:500]
    return resp.text[:300]
