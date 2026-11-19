"""Auth, dashboard, jobs, library, files, webhooks, settings, providers, usage."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import serializers as ser
from app.api.deps import can_write, current_user, owned_project, require_role
from app.api.schemas import LoginRequest, SettingUpdate, UserCreate
from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import (create_access_token, hash_password, verify_password, verify_signed_path,
                               verify_webhook_token)
from app.db.models import (ApplicationSetting, Export, GeneratedAsset, GenerationJob, Project, ProviderRequest,
                           UsageRecord, User)
from app.pipeline import costs, dispatch
from app.providers import registry
from app.services.storage import LocalStorage, get_storage

router = APIRouter(tags=["core"])


# ---------------------------------------------------------------- auth
@router.post("/api/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}}


@router.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}


@router.post("/api/users", status_code=201)
def create_user(body: UserCreate, _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "email already registered")
    u = User(email=body.email.lower(), password_hash=hash_password(body.password), full_name=body.full_name,
             role=body.role)
    db.add(u)
    db.commit()
    return {"id": u.id, "email": u.email, "role": u.role}


@router.get("/api/users")
def list_users(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active, "full_name": u.full_name}
            for u in db.scalars(select(User).order_by(User.created_at))]


# ---------------------------------------------------------------- dashboard
@router.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    own = (lambda q, col: q if user.role == "admin" else q.where(col == user.id))
    pq = own(select(Project), Project.owner_id)
    projects = db.scalars(pq).all()
    pids = [p.id for p in projects]
    exports = db.scalars(select(Export).where(Export.project_id.in_(pids))).all() if pids else []
    latest: dict[str, Export] = {}
    for e in exports:
        if e.concept_id not in latest or e.version > latest[e.concept_id].version:
            latest[e.concept_id] = e
    jobs_q = select(GenerationJob.status, func.count()).where(GenerationJob.project_id.in_(pids)).group_by(
        GenerationJob.status) if pids else None
    job_counts = dict(db.execute(jobs_q).all()) if jobs_q is not None else {}
    credits = db.scalar(select(func.coalesce(func.sum(UsageRecord.credits), 0)).where(
        UsageRecord.project_id.in_(pids))) if pids else 0
    usd = db.scalar(select(func.sum(UsageRecord.cost_usd)).where(UsageRecord.project_id.in_(pids))) if pids else None
    recent = sorted(projects, key=lambda p: p.created_at, reverse=True)[:8]
    return {
        "total_ads": len(latest),
        "completed_videos": sum(1 for e in latest.values() if e.status == "approved"),
        "needs_review": sum(1 for e in latest.values() if e.status == "qa_failed"),
        "active_jobs": sum(v for k, v in job_counts.items() if k in ("pending", "submitting", "submitted", "running")),
        "active_projects": sum(1 for p in projects if p.status in ("queued", "running")),
        "failed_jobs": job_counts.get("failed", 0),
        "failed_projects": sum(1 for p in projects if p.status == "failed"),
        "credits_spent": round(float(credits or 0), 1),
        "estimated_cost_usd": round(float(usd), 2) if usd else None,
        "global_budget_credits": get_settings().global_budget_credits,
        "global_committed_this_month": round(costs.global_committed_this_month(db), 1),
        "recent_projects": [ser.project_summary(db, p) for p in recent],
    }


# ---------------------------------------------------------------- jobs
@router.get("/api/jobs")
def list_jobs(project_id: str | None = None, status: str | None = None, user: User = Depends(current_user),
              db: Session = Depends(get_db)):
    q = select(GenerationJob).order_by(GenerationJob.created_at.desc()).limit(300)
    if project_id:
        owned_project(db, project_id, user)
        q = q.where(GenerationJob.project_id == project_id)
    elif user.role != "admin":
        q = q.join(Project, GenerationJob.project_id == Project.id).where(Project.owner_id == user.id)
    if status:
        q = q.where(GenerationJob.status == status)
    return [ser.job_out(j) for j in db.scalars(q)]


@router.get("/api/jobs/{job_id}/requests")
def job_requests(job_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    j = db.get(GenerationJob, job_id)
    if not j or (j.project_id and owned_project(db, j.project_id, user) is None):
        raise HTTPException(404, "job not found")
    return [{"operation": r.operation, "method": r.method, "endpoint": r.endpoint, "status_code": r.status_code,
             "duration_ms": r.duration_ms, "error": r.error, "response": r.response_excerpt,
             "created_at": ser.dt(r.created_at)}
            for r in db.scalars(select(ProviderRequest).where(ProviderRequest.job_id == job_id)
                                .order_by(ProviderRequest.created_at))]


@router.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    j = db.get(GenerationJob, job_id)
    if not j:
        raise HTTPException(404, "job not found")
    p = owned_project(db, j.project_id, user) if j.project_id else None
    if j.status not in ("failed", "cancelled"):
        raise HTTPException(409, f"job is {j.status}")
    j.status, j.attempts, j.error, j.provider_job_id = "pending", 0, None, None
    if p and p.status in ("failed", "cancelled"):
        p.status, p.error = "queued", None
    db.commit()
    dispatch.submit_job(j.id)
    return ser.job_out(j)


# ---------------------------------------------------------------- library
@router.get("/api/exports")
def library(status: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Export).join(Project, Export.project_id == Project.id).order_by(Export.created_at.desc())
    if user.role != "admin":
        q = q.where(Project.owner_id == user.id)
    if status:
        q = q.where(Export.status == status)
    out = []
    for e in db.scalars(q.limit(300)):
        d = ser.export_out(db, e)
        p = db.get(Project, e.project_id)
        d["project"] = {"id": p.id, "name": p.name, "language": (p.settings or {}).get("language")}
        out.append(d)
    return out


@router.get("/api/exports/{export_id}")
def get_export(export_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = db.get(Export, export_id)
    if not e:
        raise HTTPException(404, "export not found")
    p = owned_project(db, e.project_id, user)
    d = ser.export_out(db, e)
    detail = ser.project_detail(db, p)
    d["concept_detail"] = next((c for c in detail["concepts"] if c["id"] == e.concept_id), None)
    d["product"] = detail.get("product")
    d["settings"] = detail["settings"]
    d["versions"] = [ser.export_out(db, x, with_qa=False) for x in
                     db.scalars(select(Export).where(Export.concept_id == e.concept_id).order_by(Export.version))]
    d["scene_qa"] = [r for r in detail["qa_reports"] if r["scope"] == "scene"
                     and any(s["id"] == r["scene_id"] for s in (d["concept_detail"] or {}).get("storyboard", {}).get("scenes", []))]
    return d


# ---------------------------------------------------------------- signed local files
@router.get("/api/files/{key:path}")
def serve_file(key: str, exp: int = Query(...), sig: str = Query(...), dl: str | None = None):
    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        raise HTTPException(404, "not available")
    if not verify_signed_path(key, exp, sig):
        raise HTTPException(403, "invalid or expired signature")
    path = storage.local_path(key)
    try:
        return FileResponse(path, filename=dl) if dl else FileResponse(path)
    except FileNotFoundError:
        raise HTTPException(404, "file not found")


@router.get("/api/assets/{asset_id}/url")
def asset_url(asset_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = db.get(GeneratedAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    if a.project_id:
        owned_project(db, a.project_id, user)
    return {"url": ser.url(db, a.id)}


# ---------------------------------------------------------------- webhooks
@router.post("/api/webhooks/letzai/{job_id}", status_code=202)
async def letzai_webhook(job_id: str, request: Request, token: str = Query(""), db: Session = Depends(get_db)):
    """LetzAI calls webhookUrl on progress/completion. LetzAI documents no
    payload signature, so we authenticate with a per-job HMAC token in the URL
    and treat the body only as a hint: the job state is re-fetched from the API."""
    if not verify_webhook_token(job_id, token):
        raise HTTPException(403, "invalid webhook token")
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    body = await request.body()
    if len(body) > 1_000_000:
        raise HTTPException(413, "payload too large")
    if job.status in ("submitted", "running"):
        dispatch.poll_job(job.id)
    return {"accepted": True}


# ---------------------------------------------------------------- settings & providers
EDITABLE_SETTINGS = {"default_approval_checkpoints", "default_video_model", "default_budget_credits",
                     "default_language", "brand_presets"}


@router.get("/api/settings")
def get_app_settings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_settings()
    stored = {r.key: r.value for r in db.scalars(select(ApplicationSetting))}
    return {"stored": stored, "effective": {
        "media_provider": s.media_provider, "llm_provider": registry.llm_provider().name,
        "lipsync_provider": registry.lipsync_provider().name,
        "transcription_provider": registry.transcription_provider().name,
        "letzai_configured": bool(s.letzai_api_key), "anthropic_configured": bool(s.anthropic_api_key),
        "wavespeed_configured": bool(s.wavespeed_api_key), "webhooks_enabled": bool(s.webhook_base_url),
        "default_video_model": s.letzai_video_model, "default_image_model": s.letzai_image_model,
        "default_speech_model": s.letzai_speech_model, "max_qa_rounds": s.max_qa_rounds,
        "max_job_attempts": s.max_job_attempts, "default_project_budget_credits": s.default_project_budget_credits,
        "global_budget_credits": s.global_budget_credits, "max_concurrent_jobs": s.letzai_max_concurrent_jobs,
        "usd_per_credit": s.letzai_usd_per_credit, "data_retention_days": s.data_retention_days}}


@router.put("/api/settings/{key}")
def put_setting(key: str, body: SettingUpdate, user: User = Depends(require_role("admin")),
                db: Session = Depends(get_db)):
    if key not in EDITABLE_SETTINGS:
        raise HTTPException(422, f"editable keys: {sorted(EDITABLE_SETTINGS)}")
    row = db.get(ApplicationSetting, key) or ApplicationSetting(key=key)
    row.value, row.updated_by = body.value, user.id
    db.merge(row)
    db.commit()
    return {"key": key, "value": body.value}


@router.get("/api/providers/models")
def provider_models(_: User = Depends(current_user)):
    return registry.media_provider().list_models()


@router.get("/api/usage")
def usage(days: int = 30, user: User = Depends(current_user), db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(UsageRecord.provider, UsageRecord.model, UsageRecord.kind, func.count(),
               func.sum(UsageRecord.credits), func.sum(UsageRecord.cost_usd)).where(UsageRecord.created_at >= since)
    if user.role != "admin":
        q = q.join(Project, UsageRecord.project_id == Project.id).where(Project.owner_id == user.id)
    rows = db.execute(q.group_by(UsageRecord.provider, UsageRecord.model, UsageRecord.kind)).all()
    return [{"provider": a, "model": b, "kind": c, "count": n, "credits": round(cr or 0, 1),
             "cost_usd": round(u, 4) if u else None} for a, b, c, n, cr, u in rows]
