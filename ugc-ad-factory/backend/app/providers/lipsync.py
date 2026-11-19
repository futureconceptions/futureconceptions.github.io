"""Lip-sync providers. LetzAI has no public lip-sync endpoint, so this is an
interchangeable external adapter.

WaveSpeedLipSync is ported (MIT) from kofiowusuai-lab/ugc-skills
vendor/voiceswap/voiceswap/wavespeed.py: upload video+audio via
POST /media/upload/binary?ext=..., submit to POST /{model} with
{"video","audio"}, poll data.urls.get until status completed/failed.
It has not been verified against a live WaveSpeed account in this project.
"""
from __future__ import annotations

import os
import time

import httpx

from app.core.config import get_settings
from app.providers.base import LipSyncResult, ProviderError, RequestLogger, null_logger
from app.services.safe_fetch import validate_url

WAVESPEED_BASE = "https://api.wavespeed.ai/api/v3"


class NoLipSync:
    """Used when no provider is configured: the pipeline falls back to native
    model audio or a voice-over edit (and records that in the QA report)."""
    name = "none"

    def available(self) -> bool:
        return False

    def submit(self, video_path, audio_path, *, log=null_logger):  # pragma: no cover
        raise ProviderError("no lip-sync provider configured")

    def poll(self, provider_job_id, *, log=null_logger):  # pragma: no cover
        raise ProviderError("no lip-sync provider configured")

    def download(self, url, dest_path):  # pragma: no cover
        raise ProviderError("no lip-sync provider configured")


class WaveSpeedLipSync:
    name = "wavespeed"

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 transport: httpx.BaseTransport | None = None):
        s = get_settings()
        key = api_key or (s.wavespeed_api_key.get_secret_value() if s.wavespeed_api_key else None)
        if not key:
            raise ProviderError("WAVESPEED_API_KEY is not configured")
        self.model = model or s.wavespeed_model
        self.http = httpx.Client(timeout=300, transport=transport,
                                 headers={"Authorization": f"Bearer {key}"})
        self._poll_urls: dict[str, str] = {}

    def available(self) -> bool:
        return True

    def _log(self, log, op, method, url, resp, t0, req=None):
        log(operation=op, method=method, endpoint=url.split("?")[0], status_code=resp.status_code,
            duration_ms=int((time.monotonic() - t0) * 1000), request=req,
            response=None, error=None if resp.status_code < 400 else resp.text[:300])

    def _upload(self, path: str, log: RequestLogger) -> str:
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        url = f"{WAVESPEED_BASE}/media/upload/binary" + (f"?ext={ext}" if ext else "")
        t0 = time.monotonic()
        with open(path, "rb") as f:
            r = self.http.post(url, content=f.read())
        self._log(log, "wavespeed_upload", "POST", url, r, t0)
        if r.status_code >= 400:
            raise ProviderError(f"WaveSpeed upload failed: {r.status_code}", retryable=r.status_code >= 500)
        data = r.json().get("data", r.json())
        out = data.get("download_url") or data.get("url")
        if not out:
            raise ProviderError("WaveSpeed upload returned no URL")
        return out

    def submit(self, video_path: str, audio_path: str, *, log: RequestLogger = null_logger) -> str:
        body = {"video": self._upload(video_path, log), "audio": self._upload(audio_path, log)}
        url = f"{WAVESPEED_BASE}/{self.model}"
        t0 = time.monotonic()
        r = self.http.post(url, json=body)
        self._log(log, "wavespeed_submit", "POST", url, r, t0, req={"model": self.model})
        if r.status_code >= 400:
            raise ProviderError(f"WaveSpeed submit failed: {r.status_code} {r.text[:200]}",
                                retryable=r.status_code in (429, 500, 502, 503, 504))
        data = r.json().get("data", r.json())
        task_id = data["id"]
        self._poll_urls[task_id] = data.get("urls", {}).get("get") or f"{WAVESPEED_BASE}/predictions/{task_id}/result"
        return task_id

    def poll(self, provider_job_id: str, *, log: RequestLogger = null_logger) -> LipSyncResult:
        url = self._poll_urls.get(provider_job_id) or f"{WAVESPEED_BASE}/predictions/{provider_job_id}/result"
        t0 = time.monotonic()
        r = self.http.get(url)
        self._log(log, "wavespeed_poll", "GET", url, r, t0)
        if r.status_code >= 400:
            raise ProviderError(f"WaveSpeed poll failed: {r.status_code}", retryable=True)
        data = r.json().get("data", r.json())
        status = data.get("status")
        outputs = data.get("outputs") or ([data["output"]] if data.get("output") else [])
        if status == "completed" and outputs:
            return LipSyncResult(state="succeeded", output_url=outputs[0], provider_job_id=provider_job_id)
        if status in ("failed", "error"):
            return LipSyncResult(state="failed", error=str(data.get("error") or status),
                                 provider_job_id=provider_job_id)
        return LipSyncResult(state="running", provider_job_id=provider_job_id)

    def download(self, url: str, dest_path: str) -> str:
        validate_url(url)
        with httpx.Client(timeout=300, follow_redirects=True) as c, c.stream("GET", url) as r:
            if r.status_code >= 400:
                raise ProviderError(f"download failed {r.status_code}", retryable=True)
            with open(dest_path, "wb") as f:
                for chunk in r.iter_bytes(1 << 20):
                    f.write(chunk)
        return dest_path
