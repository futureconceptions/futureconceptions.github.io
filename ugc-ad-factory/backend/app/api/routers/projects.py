from __future__ import annotations

import json
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import serializers as ser
from app.api.deps import can_write, current_user, owned_creator, owned_project
from app.api.schemas import ApproveRequest, BudgetConfirm, ProjectCreate
from app.core.config import get_settings
from app.core.db import get_db
from app.db.models import AdConcept, GenerationJob, Product, ProductAsset, Project, Scene, User
from app.media import ffmpeg as ff
from app.pipeline import costs, dispatch, jobs
from app.pipeline.stages import STAGES
from app.providers import registry
from app.services.storage import get_storage, tmp_dir

router = APIRouter(prefix="/api/projects", tags=["projects"])

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGES = 8


def _parse_payload(payload: str) -> ProjectCreate:
    try:
        return ProjectCreate.model_validate(json.loads(payload))
    except (ValueError, ValidationError) as e:
        raise HTTPException(422, f"invalid project payload: {e}")


@router.post("/estimate")
def estimate(body: ProjectCreate, user: User = Depends(current_user)):
    """Pre-launch cost estimate (no provider calls, nothing is charged)."""
    try:
        return costs.estimate_project(body.pipeline_settings(), registry.media_provider(),
                                      has_creator=bool(body.creator_id))
    except KeyError as e:
        raise HTTPException(422, str(e))


@router.post("", status_code=201)
async def create_project(payload: str = Form(..., description="ProjectCreate JSON"),
                         images: list[UploadFile] = File(default=[]),
                         user: User = Depends(can_write), db: Session = Depends(get_db)):
    body = _parse_payload(payload)
    images = [i for i in images if i.filename]
    if not (body.product_url or body.product_description or images):
        raise HTTPException(422, "Provide a product URL, a description or at least one product image")
    if images and not body.assets_licensed:
        raise HTTPException(422, "Confirm that you hold the rights to the uploaded product images (assets_licensed)")
    if len(images) > MAX_IMAGES:
        raise HTTPException(422, f"At most {MAX_IMAGES} images")
    if body.creator_id:
        owned_creator(db, body.creator_id, user)
    s = get_settings()
    settings = body.pipeline_settings()
    try:
        est = costs.estimate_project(settings, registry.media_provider(), has_creator=bool(body.creator_id))
    except KeyError as e:
        raise HTTPException(422, str(e))
    budget = body.budget_credits or s.default_project_budget_credits
    over = est["total_credits"] > budget
    project = Project(owner_id=user.id, name=body.name or body.product_name or body.brand_name or "Untitled product",
                      status="awaiting_budget" if (over and not body.confirm_budget) else "queued",
                      stage="research", settings=settings, creator_id=body.creator_id, budget_credits=budget,
                      estimated_credits=est["total_credits"], budget_confirmed=body.confirm_budget,
                      stage_detail=(f"Estimated {est['total_credits']} credits exceeds budget {budget}; "
                                    "confirm to start") if (over and not body.confirm_budget) else None)
    if over and body.confirm_budget:
        project.budget_credits = max(budget, est["total_credits"])
    db.add(project)
    db.flush()
    product = Product(project_id=project.id, url=str(body.product_url) if body.product_url else None,
                      name=body.product_name, brand_name=body.brand_name, description=body.product_description,
                      brand_guidelines=body.brand_guidelines)
    db.add(product)
    db.flush()
    for up in images:
        data = await up.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(413, f"{up.filename} exceeds 15 MB")
        ctype = (up.content_type or "").lower()
        if ctype not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(415, f"{up.filename}: only JPEG, PNG or WebP images are accepted")
        fd, path = tempfile.mkstemp(dir=tmp_dir(), suffix=ALLOWED_IMAGE_TYPES[ctype])
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        try:
            info = ff.probe(path)
            if not info.has_video or not info.width:
                raise HTTPException(415, f"{up.filename} is not a valid image")
            key = f"projects/{project.id}/product/{os.urandom(8).hex()}{ALLOWED_IMAGE_TYPES[ctype]}"
            get_storage().put_file(key, path, ctype)
            db.add(ProductAsset(product_id=product.id, kind="image", storage_key=key, mime_type=ctype,
                                filename=(up.filename or "")[:300], width=info.width, height=info.height,
                                license_note="user attested rights at upload"))
        except ff.FFmpegError:
            raise HTTPException(415, f"{up.filename} could not be decoded")
        finally:
            os.unlink(path)
    db.commit()
    if project.status == "queued":
        dispatch.advance_project(project.id)
    return {"project": ser.project_summary(db, project), "estimate": est}


@router.get("")
def list_projects(status: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Project).order_by(Project.created_at.desc())
    if user.role != "admin":
        q = q.where(Project.owner_id == user.id)
    if status:
        q = q.where(Project.status == status)
    return [ser.project_summary(db, p) for p in db.scalars(q.limit(200))]


@router.get("/{project_id}")
def get_project(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return ser.project_detail(db, owned_project(db, project_id, user))


@router.get("/{project_id}/estimate")
def project_estimate(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    return costs.estimate_storyboards(db, p, registry.media_provider())


@router.post("/{project_id}/approve")
def approve(project_id: str, body: ApproveRequest, user: User = Depends(can_write), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    if body.checkpoint == "concepts" and body.selected_concept_ids is not None:
        ids = set(body.selected_concept_ids)
        concepts = db.scalars(select(AdConcept).where(AdConcept.project_id == p.id)).all()
        if not ids or not ids.issubset({c.id for c in concepts}):
            raise HTTPException(422, "selected_concept_ids must be non-empty concept ids of this project")
        for c in concepts:
            c.selected = c.id in ids
    p.approvals = {**(p.approvals or {}), body.checkpoint: {"by": user.id}}
    if p.status == "awaiting_approval":
        p.status = "queued"
    db.commit()
    dispatch.advance_project(p.id)
    return ser.project_summary(db, p)


@router.post("/{project_id}/confirm-budget")
def confirm_budget(project_id: str, body: BudgetConfirm, user: User = Depends(can_write),
                   db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    if body.budget_credits is not None:
        p.budget_credits = body.budget_credits
    elif p.estimated_credits > p.budget_credits:
        p.budget_credits = p.estimated_credits
    p.budget_confirmed = True
    if p.status == "awaiting_budget":
        p.status = "queued"
        p.stage_detail = None
    db.commit()
    dispatch.advance_project(p.id)
    return ser.project_summary(db, p)


@router.post("/{project_id}/cancel")
def cancel(project_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    if p.status in ("completed", "cancelled"):
        raise HTTPException(409, f"project already {p.status}")
    n = jobs.cancel_project_jobs(db, p.id)
    p.status = "cancelled"
    p.stage_detail = f"Cancelled by user ({n} job(s) stopped; LetzAI videos already rendering cannot be interrupted)"
    db.commit()
    return ser.project_summary(db, p)


@router.post("/{project_id}/retry")
def retry(project_id: str, stage: str | None = None, user: User = Depends(can_write), db: Session = Depends(get_db)):
    """Resume a failed/cancelled project from its current stage (or a given earlier stage)."""
    p = owned_project(db, project_id, user)
    if p.status not in ("failed", "cancelled", "awaiting_budget", "completed"):
        raise HTTPException(409, f"cannot retry a project in status {p.status}")
    if stage:
        if stage not in STAGES or STAGES.index(stage) > STAGES.index(p.stage):
            raise HTTPException(422, "stage must be the current or an earlier stage")
        p.stage = stage
    for j in db.scalars(select(GenerationJob).where(GenerationJob.project_id == p.id,
                                                    GenerationJob.status.in_(("failed", "cancelled")))):
        j.status, j.attempts, j.error, j.provider_job_id = "pending", 0, None, None
    for sc in db.scalars(select(Scene).where(Scene.project_id == p.id, Scene.status == "failed")):
        sc.status = "pending"
    for c in db.scalars(select(AdConcept).where(AdConcept.project_id == p.id)):
        if c.rank < int((p.settings or {}).get("variants", 1)):
            c.selected = True
    p.status, p.error, p.completed_at = "queued", None, None
    db.commit()
    dispatch.advance_project(p.id)
    return ser.project_summary(db, p)


@router.post("/{project_id}/scenes/{scene_id}/regenerate")
def regenerate_scene(project_id: str, scene_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    sc = db.get(Scene, scene_id)
    if not sc or sc.project_id != p.id:
        raise HTTPException(404, "scene not found")
    if p.status in ("running", "queued"):
        raise HTTPException(409, "wait for the current run to finish")
    sc.regen_round += 1
    sc.video_asset_id = sc.final_clip_asset_id = None
    sc.lipsync_status = sc.qa_status = None
    sc.status = "pending"
    if sc.audio_source == "native":
        sc.audio_asset_id = None
    p.stage, p.status, p.error, p.completed_at = "video", "queued", None, None
    db.commit()
    dispatch.advance_project(p.id)
    return ser.project_summary(db, p)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    if p.status in ("running", "queued"):
        raise HTTPException(409, "cancel the project first")
    db.delete(p)
    db.commit()
