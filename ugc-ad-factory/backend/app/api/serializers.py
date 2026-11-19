from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (AdConcept, Creator, Export, GeneratedAsset, GenerationJob, Project, QAReport,
                           Scene, Storyboard, UsageRecord)
from app.pipeline import costs
from app.pipeline.stages import STAGES
from app.services.storage import get_storage

STAGE_LABELS = {"research": "Research", "script": "Script", "character": "Character", "scenes": "Scenes",
                "video": "Video", "voice": "Voice", "lipsync": "Lip Sync", "editing": "Editing", "qa": "QA",
                "export": "Export"}


def url(db: Session, asset_id: str | None, download_name: str | None = None) -> str | None:
    if not asset_id:
        return None
    a = db.get(GeneratedAsset, asset_id)
    if not a or a.storage_key in ("pending", "deleted"):
        return None
    return get_storage().signed_url(a.storage_key, download_name=download_name)


def dt(v):
    return v.isoformat() if v else None


def job_out(j: GenerationJob) -> dict:
    return {"id": j.id, "purpose": j.purpose, "kind": j.kind, "provider": j.provider, "model": j.model,
            "status": j.status, "progress": j.progress, "attempts": j.attempts, "max_attempts": j.max_attempts,
            "round": j.round, "candidate_index": j.candidate_index, "scene_id": j.scene_id,
            "provider_job_id": j.provider_job_id, "estimated_credits": j.estimated_credits,
            "actual_credits": j.actual_credits, "error": j.error, "output_asset_id": j.output_asset_id,
            "selected": j.selected, "created_at": dt(j.created_at), "submitted_at": dt(j.submitted_at),
            "completed_at": dt(j.completed_at)}


def pipeline_view(p: Project) -> list[dict]:
    cur = STAGES.index(p.stage) if p.stage in STAGES else 0
    out = []
    for i, s in enumerate(STAGES):
        if p.status == "completed" or i < cur:
            state = "done"
        elif i == cur:
            state = {"running": "active", "queued": "active", "failed": "failed",
                     "awaiting_approval": "waiting", "awaiting_budget": "waiting",
                     "cancelled": "cancelled"}.get(p.status, "pending")
        else:
            state = "pending"
        out.append({"key": s, "label": STAGE_LABELS[s], "state": state})
    return out


def project_summary(db: Session, p: Project) -> dict:
    thumb = db.scalar(select(Export).where(Export.project_id == p.id).order_by(Export.created_at.desc()))
    return {"id": p.id, "name": p.name, "status": p.status, "stage": p.stage, "stage_detail": p.stage_detail,
            "error": p.error, "created_at": dt(p.created_at), "updated_at": dt(p.updated_at),
            "completed_at": dt(p.completed_at), "budget_credits": p.budget_credits,
            "estimated_credits": p.estimated_credits, "spent_credits": round(costs.project_spent(db, p.id), 1),
            "language": (p.settings or {}).get("language"), "variants": (p.settings or {}).get("variants"),
            "thumbnail_url": url(db, thumb.thumbnail_asset_id) if thumb else None,
            "pipeline": pipeline_view(p)}


def export_out(db: Session, e: Export, with_qa: bool = True) -> dict:
    c = db.get(AdConcept, e.concept_id)
    d = {"id": e.id, "project_id": e.project_id, "concept_id": e.concept_id, "version": e.version,
         "status": e.status, "duration": e.duration, "width": e.width, "height": e.height,
         "video_url": url(db, e.asset_id), "download_url": url(db, e.asset_id, f"ad-{c.angle}-v{e.version}.mp4"),
         "thumbnail_url": url(db, e.thumbnail_asset_id), "subtitles_url": url(db, e.subtitles_asset_id),
         "edit_settings": {k: v for k, v in (e.edit_settings or {}).items() if k != "clip_ids"},
         "created_at": dt(e.created_at), "concept": {"title": c.title, "angle": c.angle, "hook": c.hook, "cta": c.cta}}
    if with_qa:
        r = db.scalar(select(QAReport).where(QAReport.export_id == e.id).order_by(QAReport.created_at.desc()))
        d["qa"] = qa_out(r) if r else None
    return d


def qa_out(r: QAReport) -> dict:
    return {"id": r.id, "scope": r.scope, "round": r.round, "passed": r.passed, "score": r.score,
            "checks": r.checks, "issues": r.issues, "scene_id": r.scene_id, "export_id": r.export_id,
            "created_at": dt(r.created_at)}


def creator_out(db: Session, c: Creator) -> dict:
    return {"id": c.id, "name": c.name, "description": c.description, "appearance": c.appearance,
            "voice": c.voice, "status": c.status, "is_fictional": c.is_fictional,
            "likeness_consent": c.likeness_consent, "anchor_url": url(db, c.anchor_asset_id),
            "anchor_prompt": c.anchor_prompt, "generation_metadata": c.generation_metadata,
            "references": [{"id": r.id, "kind": r.kind, "url": url(db, r.asset_id), "prompt": r.prompt,
                            "identity_score": r.identity_score} for r in c.references],
            "created_at": dt(c.created_at)}


def project_detail(db: Session, p: Project) -> dict:
    d = project_summary(db, p)
    d["settings"] = {k: v for k, v in (p.settings or {}).items() if not k.startswith("_")}
    d["approvals"] = p.approvals
    d["budget_confirmed"] = p.budget_confirmed
    d["qa_round"] = p.qa_round
    prod = p.product
    if prod:
        d["product"] = {"id": prod.id, "url": prod.url, "name": prod.name, "brand_name": prod.brand_name,
                        "description": prod.description, "brand_guidelines": prod.brand_guidelines,
                        "fetch_status": prod.fetch_status, "research": prod.research,
                        "page_meta": prod.page_meta,
                        "assets": [{"id": a.id, "kind": a.kind, "filename": a.filename,
                                    "url": get_storage().signed_url(a.storage_key)} for a in prod.assets]}
    d["creator"] = creator_out(db, db.get(Creator, p.creator_id)) if p.creator_id else None
    concepts = []
    for c in db.scalars(select(AdConcept).where(AdConcept.project_id == p.id).order_by(AdConcept.rank)):
        sc = c.scripts[-1] if c.scripts else None
        sb = db.scalar(select(Storyboard).where(Storyboard.concept_id == c.id).order_by(Storyboard.version.desc()))
        scenes = []
        if sb:
            for s in sb.scenes:
                scenes.append({"id": s.id, "idx": s.idx, "beat": s.beat, "duration": s.duration,
                               "dialogue": s.dialogue, "framing": s.framing, "creator_movement": s.creator_movement,
                               "product_interaction": s.product_interaction, "environment": s.environment,
                               "required_references": s.required_references, "video_prompt": s.video_prompt,
                               "keyframe_prompt": s.keyframe_prompt, "audio_requirements": s.audio_requirements,
                               "status": s.status, "regen_round": s.regen_round, "audio_source": s.audio_source,
                               "lipsync_status": s.lipsync_status, "qa_status": s.qa_status,
                               "keyframe_url": url(db, s.keyframe_asset_id),
                               "video_url": url(db, s.final_clip_asset_id or s.video_asset_id)})
        concepts.append({"id": c.id, "angle": c.angle, "title": c.title, "hook": c.hook,
                         "core_message": c.core_message, "emotional_angle": c.emotional_angle,
                         "visual_concept": c.visual_concept, "cta": c.cta, "target_duration": c.target_duration,
                         "claims_used": c.claims_used, "score": c.score, "rank": c.rank, "selected": c.selected,
                         "script": {"id": sc.id, "version": sc.version, "language": sc.language,
                                    "full_text": sc.full_text, "beats": sc.beats, "word_count": sc.word_count} if sc else None,
                         "storyboard": {"id": sb.id, "video_model": sb.video_model, "audio_mode": sb.audio_mode,
                                        "total_duration": sb.total_duration, "notes": sb.notes, "scenes": scenes} if sb else None})
    d["concepts"] = concepts
    d["jobs"] = [job_out(j) for j in db.scalars(select(GenerationJob).where(GenerationJob.project_id == p.id)
                                                .order_by(GenerationJob.created_at))]
    d["exports"] = [export_out(db, e) for e in db.scalars(select(Export).where(Export.project_id == p.id)
                                                           .order_by(Export.created_at))]
    d["qa_reports"] = [qa_out(r) for r in db.scalars(select(QAReport).where(QAReport.project_id == p.id)
                                                      .order_by(QAReport.created_at))]
    usage = db.execute(select(UsageRecord.provider, UsageRecord.kind, func.sum(UsageRecord.credits),
                              func.sum(UsageRecord.cost_usd), func.count())
                       .where(UsageRecord.project_id == p.id).group_by(UsageRecord.provider, UsageRecord.kind)).all()
    d["usage"] = [{"provider": a, "kind": b, "credits": round(c or 0, 1), "cost_usd": round(e, 4) if e else None,
                   "count": n} for a, b, c, e, n in usage]
    return d
