"""Generation-job lifecycle.

pending ──submit──► submitting ──► submitted/running ──poll──► succeeded
   ▲                    │                          │
   └──── retry (attempts < max, retryable) ◄───────┴──► failed / cancelled

Guarantees:
* Idempotent creation: unique idempotency_key -> the same logical job is
  never created twice (duplicate-job prevention).
* Single submission: compare-and-set pending->submitting, so concurrent
  workers cannot submit the same job twice.
* Budget + concurrency gates run immediately before every submission.
* A job is only `succeeded` after the provider reports a terminal success
  state AND the output was downloaded and stored.
"""
from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import session_scope
from app.core.logging import get_logger
from app.core.security import webhook_token
from app.db.models import GeneratedAsset, GenerationJob, Project, ProviderRequest, utcnow
from app.media import ffmpeg as ff
from app.pipeline import costs, dispatch
from app.providers import registry
from app.providers.base import MediaRequest, ProviderError
from app.services.storage import ext_for_mime, get_storage, sha256_file, tmp_dir

log = get_logger("jobs")

TERMINAL = ("succeeded", "failed", "cancelled")
IN_FLIGHT = ("submitting", "submitted", "running")
NON_RETRYABLE_MARKERS = ("not_allowed", "content policy", "nsfw", "moderation", "does not support")


def request_logger(job_id: str | None, project_id: str | None, provider: str):
    """Persist every provider call in its own transaction (survives rollbacks)."""
    def _log(*, operation, method=None, endpoint=None, status_code=None, duration_ms=None,
             request=None, response=None, error=None, **_):
        try:
            with session_scope() as db:
                db.add(ProviderRequest(job_id=job_id, project_id=project_id, provider=provider,
                                       operation=operation, method=method, endpoint=endpoint,
                                       status_code=status_code, duration_ms=duration_ms,
                                       request_excerpt=request, response_excerpt=response, error=error))
        except Exception:  # noqa: BLE001 - logging must never break the pipeline
            log.warning("provider_request_log_failed", operation=operation)
    return _log


# ---------------------------------------------------------------- creation
def create_job(db: Session, *, project_id: str | None, purpose: str, kind: str, request: dict,
               idempotency_key: str, scene_id: str | None = None, creator_id: str | None = None,
               candidate_index: int = 0, round: int = 0, provider: str | None = None,
               model: str | None = None) -> GenerationJob:
    existing = db.scalar(select(GenerationJob).where(GenerationJob.idempotency_key == idempotency_key))
    if existing:
        return existing
    s = get_settings()
    if kind == "lipsync":
        provider = provider or registry.lipsync_provider().name
        estimated = 0.0
    else:
        media = registry.media_provider()
        provider = provider or media.name
        estimated = media.estimate_credits(MediaRequest.from_dict(request))
    job = GenerationJob(project_id=project_id, purpose=purpose, kind=kind, provider=provider, model=model,
                        request_payload=request, idempotency_key=idempotency_key, scene_id=scene_id,
                        creator_id=creator_id, candidate_index=candidate_index, round=round,
                        max_attempts=s.max_job_attempts, estimated_credits=estimated)
    db.add(job)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return db.scalar(select(GenerationJob).where(GenerationJob.idempotency_key == idempotency_key))
    return job


def idem_key(*parts) -> str:
    raw = ":".join(str(p) for p in parts)
    return raw if len(raw) <= 250 else hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------- assets
def store_file(db: Session, path: str, *, project_id: str | None, kind: str, job_id: str | None = None,
               provider_url: str | None = None, mime: str | None = None, meta: dict | None = None,
               key_prefix: str | None = None) -> GeneratedAsset:
    mime = mime or mimetypes.guess_type(path)[0] or "application/octet-stream"
    asset = GeneratedAsset(project_id=project_id, job_id=job_id, kind=kind, mime_type=mime,
                           provider_url=provider_url, meta=meta or {}, storage_key="pending")
    db.add(asset)
    db.flush()
    ext = os.path.splitext(path)[1] or ext_for_mime(mime)
    asset.storage_key = f"{key_prefix or ('projects/' + project_id if project_id else 'shared')}/{kind}/{asset.id}{ext}"
    get_storage().put_file(asset.storage_key, path, mime)
    asset.size_bytes = os.path.getsize(path)
    asset.sha256 = sha256_file(path)
    if mime.startswith(("video/", "audio/", "image/")):
        try:
            info = ff.probe(path)
            asset.width, asset.height = info.width, info.height
            asset.duration = info.duration or None
            asset.meta = {**asset.meta, "has_audio": info.has_audio, "vcodec": info.vcodec,
                          "acodec": info.acodec, "fps": info.fps}
        except ff.FFmpegError:
            pass
    return asset


def local_copy(asset_key: str, suffix: str = "") -> str:
    fd, path = tempfile.mkstemp(dir=tmp_dir(), suffix=suffix or os.path.splitext(asset_key)[1])
    os.close(fd)
    return get_storage().download_to(asset_key, path)


def ensure_provider_url(db: Session, *, storage_key: str, mime: str, current: str | None,
                        project_id: str | None) -> str:
    """Return a URL the media provider can read (uploading via /user-assets if needed)."""
    media = registry.media_provider()
    if current and ((media.name == "mock") == current.startswith("mock://")):
        return current
    path = local_copy(storage_key)
    try:
        return media.upload_asset(path, mime, log=request_logger(None, project_id, media.name))
    finally:
        os.unlink(path)


# ---------------------------------------------------------------- submit
def submit_job(job_id: str) -> None:
    s = get_settings()
    with session_scope() as db:
        job = db.get(GenerationJob, job_id)
        if not job or job.status != "pending":
            return
        project = db.get(Project, job.project_id) if job.project_id else None
        if project and project.status in ("cancelled", "failed"):
            job.status = "cancelled"
            return
        # concurrency gate (soft limit shared by all workers)
        inflight = db.scalar(select(func.count()).select_from(GenerationJob).where(
            GenerationJob.provider == job.provider, GenerationJob.status.in_(IN_FLIGHT))) or 0
        if inflight >= s.letzai_max_concurrent_jobs:
            dispatch.submit_job(job.id, delay=s.poll_interval_seconds * 2)
            return
        # budget gate
        if job.estimated_credits:
            try:
                if project is not None:
                    costs.check_budget(db, project, job.estimated_credits, exclude_job=job.id)
                else:
                    costs.check_budget_global(db, job.estimated_credits)
            except costs.BudgetExceeded as e:
                job.error = str(e)
                if project is not None:
                    project.status = "awaiting_budget"
                    project.stage_detail = str(e)
                else:
                    job.status = "failed"
                return
        # compare-and-set: only one worker may submit
        res = db.execute(update(GenerationJob).where(GenerationJob.id == job.id, GenerationJob.status == "pending")
                         .values(status="submitting", attempts=GenerationJob.attempts + 1, updated_at=utcnow()))
        if res.rowcount != 1:
            return
        db.commit()
        db.refresh(job)
        _do_submit(db, job)


def _do_submit(db: Session, job: GenerationJob) -> None:
    s = get_settings()
    logger = request_logger(job.id, job.project_id, job.provider)
    try:
        if job.kind == "lipsync":
            lip = registry.lipsync_provider()
            p = job.request_payload
            vpath, apath = local_copy(p["video_key"]), local_copy(p["audio_key"])
            try:
                job.provider_job_id = lip.submit(vpath, apath, log=logger)
            finally:
                os.unlink(vpath)
                os.unlink(apath)
        else:
            req = MediaRequest.from_dict(job.request_payload)
            if s.webhook_base_url and job.provider == "letzai":
                req.webhook_url = (f"{s.webhook_base_url.rstrip('/')}/api/webhooks/letzai/{job.id}"
                                   f"?token={webhook_token(job.id)}")
            res = registry.media_provider().submit(req, log=logger)
            job.provider_job_id = res.provider_job_id
        job.status = "submitted"
        job.submitted_at = utcnow()
        job.error = None
        job.next_poll_at = utcnow() + timedelta(seconds=s.poll_interval_seconds)
        db.commit()
        dispatch.poll_job(job.id, delay=s.poll_interval_seconds)
    except (ProviderError, ValueError, ff.FFmpegError) as e:
        db.rollback()
        job = db.get(GenerationJob, job.id)
        retryable = getattr(e, "retryable", False)
        _handle_failure(db, job, str(e), retryable=retryable)


# ---------------------------------------------------------------- poll
def poll_job(job_id: str) -> None:
    s = get_settings()
    with session_scope() as db:
        job = db.get(GenerationJob, job_id)
        if not job or job.status not in ("submitted", "running") or not job.provider_job_id:
            return
        logger = request_logger(job.id, job.project_id, job.provider)
        try:
            if job.kind == "lipsync":
                r = registry.lipsync_provider().poll(job.provider_job_id, log=logger)
                state, url, err, credits, progress, meta = r.state, r.output_url, r.error, None, 0, {}
            else:
                r = registry.media_provider().poll(job.kind, job.provider_job_id, log=logger)
                state, url, err, credits, progress, meta = (r.state, r.output_url, r.error, r.credits,
                                                            r.progress, r.meta)
        except ProviderError as e:
            if e.retryable and (job.poll_errors or 0) < 20:
                job.poll_errors = (job.poll_errors or 0) + 1
                job.error = f"poll error (will retry): {e}"
                dispatch.poll_job(job.id, delay=_poll_delay(job))
                return
            _handle_failure(db, job, f"poll failed: {e}", retryable=False)
            return

        if state == "running":
            job.status = "running"
            job.progress = progress
            elapsed = (utcnow() - _aware(job.submitted_at or utcnow())).total_seconds()
            if elapsed > s.poll_timeout_seconds:
                _handle_failure(db, job, f"timed out after {int(elapsed)}s", retryable=True)
                return
            delay = _poll_delay(job)
            job.next_poll_at = utcnow() + timedelta(seconds=delay)
            dispatch.poll_job(job.id, delay=delay)
            return
        if state == "failed":
            low = (err or "").lower()
            _handle_failure(db, job, err or "generation failed",
                            retryable=not any(m in low for m in NON_RETRYABLE_MARKERS))
            return
        # succeeded: download + store before declaring success
        try:
            _finalize_success(db, job, url, credits, meta)
        except (ProviderError, ff.FFmpegError, OSError) as e:
            db.rollback()
            job = db.get(GenerationJob, job_id)
            job.error = f"download/store failed: {e}"
            job.poll_errors = (job.poll_errors or 0) + 1
            if job.poll_errors < 5:
                dispatch.poll_job(job.id, delay=_poll_delay(job))
            else:
                _handle_failure(db, job, job.error, retryable=False)
            return
    _notify_project(job_id)


def _finalize_success(db: Session, job: GenerationJob, url: str | None, credits, meta: dict) -> None:
    if not url:
        raise ProviderError("provider reported success without an output URL")
    suffix = {"image": ".png", "image_edit": ".png", "video": ".mp4", "speech": ".mp3",
              "music": ".mp3", "lipsync": ".mp4"}.get(job.kind, "")
    url_ext = os.path.splitext(url.split("?")[0])[1]
    fd, path = tempfile.mkstemp(dir=tmp_dir(), suffix=url_ext or suffix)
    os.close(fd)
    try:
        if job.kind == "lipsync":
            registry.lipsync_provider().download(url, path)
        else:
            registry.media_provider().download(url, path)
        kind = {"image_edit": "image", "speech": "audio", "music": "audio", "lipsync": "video"}.get(job.kind, job.kind)
        is_creator_asset = job.purpose == "anchor" and job.creator_id
        asset = store_file(db, path, project_id=None if is_creator_asset else job.project_id, kind=kind,
                           job_id=job.id, provider_url=url if job.kind != "lipsync" else None,
                           key_prefix=f"creators/{job.creator_id}" if is_creator_asset else None,
                           meta={"provider": job.provider, "purpose": job.purpose, **(meta or {})})
    finally:
        if os.path.exists(path):
            os.unlink(path)
    job.output_asset_id = asset.id
    job.output_url = url
    job.status = "succeeded"
    job.progress = 100
    job.completed_at = utcnow()
    job.error = None
    job.actual_credits = float(credits) if credits is not None else job.estimated_credits
    costs.record_usage(db, project_id=job.project_id, job_id=job.id, provider=job.provider, model=job.model,
                       kind=job.kind, credits=job.actual_credits, estimated=credits is None)
    if job.purpose == "anchor" and job.creator_id:
        _attach_anchor(db, job, asset)


def _attach_anchor(db: Session, job: GenerationJob, asset: GeneratedAsset) -> None:
    """First successful anchor becomes the creator's identity reference."""
    from app.db.models import Creator, CreatorReference
    creator = db.get(Creator, job.creator_id)
    if creator is None:
        return
    first = creator.anchor_asset_id is None
    if first:
        creator.anchor_asset_id = asset.id
        creator.status = "ready"
        job.selected = True
    db.add(CreatorReference(creator_id=creator.id, kind="anchor" if first else "variant", asset_id=asset.id,
                            storage_key=asset.storage_key, provider_url=job.output_url,
                            prompt=creator.anchor_prompt))


def _handle_failure(db: Session, job: GenerationJob, error: str, *, retryable: bool) -> None:
    job.error = error[:2000]
    if retryable and job.attempts < job.max_attempts:
        job.status = "pending"
        job.provider_job_id = None
        delay = min(300, 5 * (2 ** max(0, job.attempts - 1)))
        db.commit()
        log.info("job_retry", job_id=job.id, attempt=job.attempts, delay=delay, error=error[:200])
        dispatch.submit_job(job.id, delay=delay)
        return
    job.status = "failed"
    job.completed_at = utcnow()
    db.commit()
    log.warning("job_failed", job_id=job.id, error=error[:300])
    _notify_project(job.id)


def _notify_project(job_id: str) -> None:
    with session_scope() as db:
        job = db.get(GenerationJob, job_id)
        if job and job.project_id:
            dispatch.advance_project(job.project_id)


def _poll_delay(job: GenerationJob) -> float:
    base = get_settings().poll_interval_seconds
    if not job.submitted_at:
        return base
    elapsed = (utcnow() - _aware(job.submitted_at)).total_seconds()
    return min(30.0, base * (1 + elapsed / 60))


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def cancel_project_jobs(db: Session, project_id: str) -> int:
    """LetzAI has no video interruption endpoint; images can be interrupted.
    We stop tracking in-flight jobs and never download their output."""
    jobs = db.scalars(select(GenerationJob).where(GenerationJob.project_id == project_id,
                                                  GenerationJob.status.in_(("pending",) + IN_FLIGHT))).all()
    media = registry.media_provider()
    for j in jobs:
        if j.provider == "letzai" and j.kind == "image" and j.provider_job_id:
            try:
                media.client.interrupt_image(j.provider_job_id,
                                             log=request_logger(j.id, project_id, "letzai"))
            except Exception:  # noqa: BLE001
                pass
        j.status = "cancelled"
        j.completed_at = utcnow()
    return len(jobs)
