"""Cost estimation, spending limits and usage recording."""
from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import GenerationJob, Project, Scene, Storyboard, AdConcept, UsageRecord
from app.providers.base import LLMUsage, MediaRequest

ACTIVE = ("pending", "submitting", "submitted", "running")


class BudgetExceeded(RuntimeError):
    def __init__(self, scope: str, needed: float, limit: float, spent: float):
        super().__init__(f"{scope} budget exceeded: needs {needed:.0f} credits, "
                         f"{spent:.0f} of {limit:.0f} already committed")
        self.scope, self.needed, self.limit, self.spent = scope, needed, limit, spent


def project_committed(db: Session, project_id: str, exclude_job: str | None = None) -> float:
    spent = db.scalar(select(func.coalesce(func.sum(UsageRecord.credits), 0))
                      .where(UsageRecord.project_id == project_id)) or 0
    q = select(func.coalesce(func.sum(GenerationJob.estimated_credits), 0)).where(
        GenerationJob.project_id == project_id, GenerationJob.status.in_(("submitting", "submitted", "running")))
    if exclude_job:
        q = q.where(GenerationJob.id != exclude_job)
    return float(spent) + float(db.scalar(q) or 0)


def project_spent(db: Session, project_id: str) -> float:
    return float(db.scalar(select(func.coalesce(func.sum(UsageRecord.credits), 0))
                           .where(UsageRecord.project_id == project_id)) or 0)


def global_committed_this_month(db: Session) -> float:
    start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spent = db.scalar(select(func.coalesce(func.sum(UsageRecord.credits), 0))
                      .where(UsageRecord.created_at >= start)) or 0
    inflight = db.scalar(select(func.coalesce(func.sum(GenerationJob.estimated_credits), 0))
                         .where(GenerationJob.status.in_(("submitting", "submitted", "running")))) or 0
    return float(spent) + float(inflight)


def check_budget(db: Session, project: Project, additional: float, exclude_job: str | None = None) -> None:
    s = get_settings()
    committed = project_committed(db, project.id, exclude_job)
    if committed + additional > project.budget_credits:
        raise BudgetExceeded("project", additional, project.budget_credits, committed)
    g = global_committed_this_month(db)
    if g + additional > s.global_budget_credits:
        raise BudgetExceeded("global", additional, s.global_budget_credits, g)


def check_budget_global(db: Session, additional: float) -> None:
    s = get_settings()
    g = global_committed_this_month(db)
    if g + additional > s.global_budget_credits:
        raise BudgetExceeded("global", additional, s.global_budget_credits, g)


def record_usage(db: Session, *, project_id: str | None, job_id: str | None, provider: str, model: str | None,
                 kind: str, credits: float, units: float = 1, unit: str | None = None,
                 estimated: bool = False, cost_usd: float | None = None) -> UsageRecord:
    s = get_settings()
    if cost_usd is None and s.letzai_usd_per_credit and provider in ("letzai", "mock"):
        cost_usd = credits * s.letzai_usd_per_credit
    rec = UsageRecord(project_id=project_id, job_id=job_id, provider=provider, model=model, kind=kind,
                      credits=credits, units=units, unit=unit, estimated=estimated, cost_usd=cost_usd)
    db.add(rec)
    return rec


def record_llm_usage(db: Session, project_id: str | None, usage: LLMUsage, task: str) -> None:
    if usage.model == "heuristic" or (usage.input_tokens == 0 and usage.output_tokens == 0):
        return
    record_usage(db, project_id=project_id, job_id=None, provider="anthropic", model=usage.model,
                 kind=f"llm:{task}", credits=0, units=usage.input_tokens + usage.output_tokens,
                 unit="tokens", cost_usd=usage.cost_usd)


# ---------------------------------------------------------------- estimates
def estimate_project(settings: dict, media, *, has_creator: bool) -> dict:
    """Pre-launch estimate (before research) from the requested settings."""
    s = get_settings()
    info = media.video_model(settings.get("video_model") or s.letzai_video_model)
    variants = int(settings.get("variants", 2))
    duration = float(settings.get("duration", 20))
    candidates = int(settings.get("video_candidates", s.default_video_candidates))
    resolution = settings.get("resolution") or s.letzai_video_resolution
    audio_mode = settings.get("audio_mode") or ("native" if info.native_audio else "tts")
    scene_len = max(info.min_duration, min(info.max_duration, 6))
    scenes_per_ad = max(1, math.ceil(duration / scene_len))
    per_scene_secs = max(info.min_duration, duration / scenes_per_ad)
    lines: list[dict] = []
    if not has_creator:
        c = media.estimate_credits(MediaRequest(kind="image", model=settings.get("image_model")))
        lines.append({"item": "creator anchor image", "qty": 1, "credits": c})
    kf = media.estimate_credits(MediaRequest(kind="image_edit", model=settings.get("image_model")))
    lines.append({"item": "scene keyframes (image edit)", "qty": variants * scenes_per_ad,
                  "credits": kf * variants * scenes_per_ad})
    v = media.estimate_credits(MediaRequest(kind="video", model=info.key, duration=int(round(per_scene_secs)),
                                            resolution=resolution, with_audio=audio_mode == "native"))
    lines.append({"item": f"scene videos ({info.display_name})", "qty": variants * scenes_per_ad * candidates,
                  "credits": v * variants * scenes_per_ad * candidates})
    if audio_mode == "tts":
        chars = int(duration * 2.5 * 6)
        sp = media.estimate_credits(MediaRequest(kind="speech", text="x" * chars))
        lines.append({"item": "voice (speech synthesis)", "qty": variants, "credits": sp * variants})
    subtotal = sum(l["credits"] for l in lines)
    contingency = subtotal * 0.25 * min(1, s.max_qa_rounds)
    lines.append({"item": "QA regeneration contingency (25%)", "qty": 1, "credits": contingency})
    total = subtotal + contingency
    return {"total_credits": round(total), "lines": lines, "video_model": info.key, "audio_mode": audio_mode,
            "scenes_per_ad": scenes_per_ad, "usd": round(total * s.letzai_usd_per_credit, 2)
            if s.letzai_usd_per_credit else None, "basis": "LetzAI catalogue list prices (estimate)"}


def estimate_storyboards(db: Session, project: Project, media) -> dict:
    """Exact-shape estimate once storyboards exist (excludes work already done)."""
    s = get_settings()
    st = project.settings or {}
    candidates = int(st.get("video_candidates", s.default_video_candidates))
    total = 0.0
    lines = []
    rows = db.execute(select(Scene, Storyboard).join(Storyboard, Scene.storyboard_id == Storyboard.id)
                      .join(AdConcept, Storyboard.concept_id == AdConcept.id)
                      .where(Scene.project_id == project.id, AdConcept.selected.is_(True))).all()
    for scene, sb in rows:
        if scene.video_asset_id:
            continue
        v = media.estimate_credits(MediaRequest(kind="video", model=sb.video_model, duration=int(math.ceil(scene.duration)),
                                                resolution=st.get("resolution") or s.letzai_video_resolution,
                                                with_audio=sb.audio_mode == "native")) * candidates
        k = 0 if scene.keyframe_asset_id else media.estimate_credits(MediaRequest(kind="image_edit"))
        a = media.estimate_credits(MediaRequest(kind="speech", text=scene.dialogue)) if (
            sb.audio_mode == "tts" and scene.dialogue) else 0
        total += v + k + a
        lines.append({"scene": scene.id, "video": v, "keyframe": k, "speech": a})
    committed = project_committed(db, project.id)
    return {"remaining_credits": round(total), "committed_credits": round(committed),
            "projected_total": round(total + committed), "lines": lines}
