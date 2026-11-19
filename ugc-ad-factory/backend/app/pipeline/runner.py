"""Entry points executed by workers (Celery tasks or the inline dispatcher)."""
from __future__ import annotations

import traceback
import uuid
from datetime import timedelta

from sqlalchemy import or_, select, update

from app.core.db import session_scope
from app.core.logging import get_logger
from app.db.models import GenerationJob, Project, utcnow
from app.pipeline import dispatch, jobs
from app.pipeline.stages import DONE, PAUSE, STAGE_FUNCS, STAGES, WAIT, Ctx, StageFailed
from app.providers.base import ProviderError

log = get_logger("runner")
LEASE_SECONDS = 15 * 60
RUNNABLE = ("queued", "running")
MAX_TRANSIENT_RETRIES = 5


def submit_job(job_id: str) -> None:
    jobs.submit_job(job_id)


def poll_job(job_id: str) -> None:
    jobs.poll_job(job_id)


def _acquire(project_id: str) -> str | None:
    token = uuid.uuid4().hex
    now = utcnow()
    with session_scope() as db:
        res = db.execute(update(Project).where(
            Project.id == project_id, Project.status.in_(RUNNABLE),
            or_(Project.lease_expires_at.is_(None), Project.lease_expires_at < now))
            .values(lease_owner=token, lease_expires_at=now + timedelta(seconds=LEASE_SECONDS)))
        return token if res.rowcount == 1 else None


def _release(project_id: str, token: str) -> None:
    with session_scope() as db:
        db.execute(update(Project).where(Project.id == project_id, Project.lease_owner == token)
                   .values(lease_owner=None, lease_expires_at=None))


def advance_project(project_id: str) -> None:
    with session_scope() as db:
        p = db.get(Project, project_id)
        if not p or p.status not in RUNNABLE:
            return
    token = _acquire(project_id)
    if token is None:
        # another worker holds the lease: try again shortly so no event is lost
        dispatch.advance_project(project_id, delay=5)
        return
    try:
        _run_stages(project_id)
    finally:
        _release(project_id, token)


def _run_stages(project_id: str) -> None:
    for _ in range(len(STAGES) * 4):  # bounded loop (regeneration rounds jump back)
        with session_scope() as db:
            project = db.get(Project, project_id)
            if project.status not in RUNNABLE:
                return
            project.status = "running"
            stage = project.stage
            ctx = Ctx(db=db, project=project)
            try:
                result = STAGE_FUNCS[stage](ctx)
            except StageFailed as e:
                project.status = "failed"
                project.error = f"[{stage}] {e}"
                log.warning("project_failed", project_id=project_id, stage=stage, error=str(e))
                return
            except ProviderError as e:
                db.rollback()
                _transient_or_fail(project_id, stage, e, e.retryable)
                return
            except Exception as e:  # noqa: BLE001
                db.rollback()
                log.error("stage_crashed", project_id=project_id, stage=stage, error=str(e),
                          tb=traceback.format_exc()[-2000:])
                _transient_or_fail(project_id, stage, e, retryable=False)
                return
            log.info("stage_result", project_id=project_id, stage=stage, result=result)
            if result == WAIT:
                return
            if result == PAUSE:
                project.status = "awaiting_approval"
                return
            if result == "pause_budget":
                project.status = "awaiting_budget"
                return
            if result.startswith("goto:"):
                project.stage = result.split(":", 1)[1]
                continue
            assert result == DONE
            project.error = None
            if "_retries" in (project.settings or {}):
                project.settings = {k: v for k, v in project.settings.items() if k != "_retries"}
            idx = STAGES.index(stage)
            if idx + 1 >= len(STAGES):
                project.status = "completed"
                project.stage = "export"
                return
            project.stage = STAGES[idx + 1]
            project.stage_detail = None


def _transient_or_fail(project_id: str, stage: str, err: Exception, retryable: bool) -> None:
    with session_scope() as db:
        p = db.get(Project, project_id)
        st = dict(p.settings or {})
        n = int(st.get("_retries", 0)) + 1
        if retryable and n <= MAX_TRANSIENT_RETRIES:
            st["_retries"] = n
            p.settings = st
            p.stage_detail = f"Transient error in {stage}, retry {n}/{MAX_TRANSIENT_RETRIES}: {err}"[:500]
            dispatch.advance_project(project_id, delay=min(300, 10 * 2 ** n))
        else:
            p.status = "failed"
            p.error = f"[{stage}] {err}"[:2000]


def recover_stale() -> dict:
    """Periodic safety net (Celery beat): re-poll overdue jobs, resubmit
    pending jobs and nudge running projects. Makes the system self-healing
    after worker crashes or lost queue messages."""
    now = utcnow()
    counts = {"polled": 0, "submitted": 0, "advanced": 0}
    with session_scope() as db:
        overdue = db.scalars(select(GenerationJob.id).where(
            GenerationJob.status.in_(("submitted", "running")),
            or_(GenerationJob.next_poll_at.is_(None), GenerationJob.next_poll_at < now - timedelta(seconds=60))))
        for jid in overdue:
            dispatch.poll_job(jid)
            counts["polled"] += 1
        stuck_submitting = db.scalars(select(GenerationJob).where(
            GenerationJob.status == "submitting", GenerationJob.updated_at < now - timedelta(minutes=10)))
        for j in stuck_submitting:
            # submission outcome unknown: mark failed rather than risk a duplicate paid job
            j.status = "failed"
            j.error = "submission interrupted; outcome unknown (not resubmitted to avoid duplicate charges)"
        pending = db.scalars(select(GenerationJob.id).where(
            GenerationJob.status == "pending", GenerationJob.updated_at < now - timedelta(minutes=2)))
        for jid in pending:
            dispatch.submit_job(jid)
            counts["submitted"] += 1
        running = db.scalars(select(Project.id).where(
            Project.status.in_(RUNNABLE), Project.updated_at < now - timedelta(minutes=2)))
        for pid in running:
            dispatch.advance_project(pid)
            counts["advanced"] += 1
    return counts
