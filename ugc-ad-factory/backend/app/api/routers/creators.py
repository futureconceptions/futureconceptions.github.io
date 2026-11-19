from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.creator_director import anchor_prompt
from app.agents.schemas import CreatorSpec
from app.agents.video_producer import anchor_request
from app.api import serializers as ser
from app.api.deps import can_write, current_user, owned_creator
from app.api.schemas import CreatorCreate
from app.core.config import get_settings
from app.core.db import get_db
from app.db.models import Creator, CreatorReference, GenerationJob, User
from app.media import ffmpeg as ff
from app.pipeline import costs, dispatch, jobs
from app.services.storage import tmp_dir

router = APIRouter(prefix="/api/creators", tags=["creators"])


def _anchor_prompt_for(c: Creator) -> str:
    try:
        return anchor_prompt(CreatorSpec.model_validate(c.appearance))
    except Exception:  # noqa: BLE001 - free-form appearance
        bits = [c.description or c.name] + [f"{k}: {v}" for k, v in (c.appearance or {}).items()]
        from app.agents import prompts as P
        return P.clean_prompt(f"Portrait of a fictional person, {'; '.join(bits)}. Looking into the lens. "
                              f"{P.REALISM} {P.NO_TEXT}")


@router.get("")
def list_creators(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Creator).order_by(Creator.created_at.desc())
    if user.role != "admin":
        q = q.where(Creator.owner_id == user.id)
    return [ser.creator_out(db, c) for c in db.scalars(q)]


@router.post("", status_code=201)
def create_creator(body: CreatorCreate, user: User = Depends(can_write), db: Session = Depends(get_db)):
    c = Creator(owner_id=user.id, name=body.name, description=body.description, appearance=body.appearance,
                voice={"preset": body.voice_preset, "language": body.language,
                       "model": get_settings().letzai_speech_model},
                is_fictional=body.is_fictional, status="draft",
                likeness_consent=None if body.is_fictional else {
                    "person": body.consent_person_name, "reference": body.consent_reference,
                    "confirmed": True, "confirmed_by": user.id})
    db.add(c)
    db.flush()
    c.anchor_prompt = _anchor_prompt_for(c)
    db.commit()
    if body.generate_anchor and body.is_fictional:
        _start_anchor(db, c)
    return ser.creator_out(db, c)


def _start_anchor(db: Session, c: Creator) -> GenerationJob:
    req = anchor_request(prompt=c.anchor_prompt, model=None)
    n = len(db.scalars(select(GenerationJob).where(GenerationJob.creator_id == c.id,
                                                   GenerationJob.purpose == "anchor")).all())
    job = jobs.create_job(db, project_id=None, purpose="anchor", kind="image", request=req.to_dict(),
                          creator_id=c.id, model=get_settings().letzai_image_model,
                          idempotency_key=jobs.idem_key("anchor", c.id, "lib", n))
    try:
        costs.check_budget_global(db, job.estimated_credits)
    except costs.BudgetExceeded as e:
        raise HTTPException(402, str(e))
    c.status = "generating"
    db.commit()
    dispatch.submit_job(job.id)
    return job


@router.get("/{creator_id}")
def get_creator(creator_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = owned_creator(db, creator_id, user)
    d = ser.creator_out(db, c)
    d["jobs"] = [ser.job_out(j) for j in db.scalars(select(GenerationJob).where(GenerationJob.creator_id == c.id))]
    return d


@router.post("/{creator_id}/regenerate-anchor")
def regenerate_anchor(creator_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    """Replace the creator's look: generates a new anchor image."""
    c = owned_creator(db, creator_id, user)
    if not c.is_fictional:
        raise HTTPException(409, "real-person creators use uploaded, consented reference images only")
    c.anchor_asset_id = None
    db.flush()
    job = _start_anchor(db, c)
    return {"creator": ser.creator_out(db, c), "job": ser.job_out(job)}


@router.post("/{creator_id}/approve")
def approve_creator(creator_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    c = owned_creator(db, creator_id, user)
    if not c.anchor_asset_id:
        raise HTTPException(409, "creator has no anchor image yet")
    c.status = "approved"
    db.commit()
    return ser.creator_out(db, c)


@router.post("/{creator_id}/references", status_code=201)
async def upload_reference(creator_id: str, image: UploadFile = File(...), set_as_anchor: bool = False,
                           user: User = Depends(can_write), db: Session = Depends(get_db)):
    """Upload a reference image (licensed or consented). For real-person
    creators this is the only way to define the identity."""
    c = owned_creator(db, creator_id, user)
    ctype = (image.content_type or "").lower()
    if ctype not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(415, "JPEG, PNG or WebP only")
    data = await image.read(15 * 1024 * 1024 + 1)
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "image too large")
    fd, path = tempfile.mkstemp(dir=tmp_dir(), suffix={"image/jpeg": ".jpg", "image/png": ".png"}.get(ctype, ".webp"))
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    try:
        if not ff.probe(path).width:
            raise HTTPException(415, "not a valid image")
        asset = jobs.store_file(db, path, project_id=None, kind="image", mime=ctype,
                                key_prefix=f"creators/{c.id}", meta={"uploaded_by": user.id})
    except ff.FFmpegError:
        raise HTTPException(415, "image could not be decoded")
    finally:
        os.unlink(path)
    db.add(CreatorReference(creator_id=c.id, kind="uploaded", asset_id=asset.id, storage_key=asset.storage_key))
    if set_as_anchor or not c.anchor_asset_id:
        c.anchor_asset_id = asset.id
        c.status = "ready"
    db.commit()
    db.refresh(c)
    return ser.creator_out(db, c)


@router.delete("/{creator_id}", status_code=204)
def delete_creator(creator_id: str, user: User = Depends(can_write), db: Session = Depends(get_db)):
    c = owned_creator(db, creator_id, user)
    db.delete(c)
    db.commit()
