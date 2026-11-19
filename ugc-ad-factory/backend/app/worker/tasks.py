from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import session_scope
from app.core.logging import get_logger
from app.db.models import GeneratedAsset, Project, utcnow
from app.pipeline import runner
from app.services.storage import get_storage
from app.worker.celery_app import celery_app

log = get_logger("tasks")


@celery_app.task(name="app.worker.tasks.advance_project")
def advance_project(project_id: str) -> None:
    runner.advance_project(project_id)


@celery_app.task(name="app.worker.tasks.poll_job")
def poll_job(job_id: str) -> None:
    runner.poll_job(job_id)


@celery_app.task(name="app.worker.tasks.submit_job")
def submit_job(job_id: str) -> None:
    runner.submit_job(job_id)


@celery_app.task(name="app.worker.tasks.recover_stale")
def recover_stale() -> dict:
    return runner.recover_stale()


@celery_app.task(name="app.worker.tasks.apply_retention")
def apply_retention() -> int:
    """Delete stored media of finished projects older than DATA_RETENTION_DAYS
    (0 disables). Database rows are kept for cost/audit history."""
    days = get_settings().data_retention_days
    if days <= 0:
        return 0
    cutoff = utcnow() - timedelta(days=days)
    removed = 0
    storage = get_storage()
    with session_scope() as db:
        pids = db.scalars(select(Project.id).where(Project.status.in_(("completed", "failed", "cancelled")),
                                                   Project.updated_at < cutoff))
        for pid in pids:
            for a in db.scalars(select(GeneratedAsset).where(GeneratedAsset.project_id == pid,
                                                             GeneratedAsset.storage_key != "deleted")):
                try:
                    storage.delete(a.storage_key)
                except Exception:  # noqa: BLE001
                    log.warning("retention_delete_failed", key=a.storage_key)
                    continue
                a.meta = {**(a.meta or {}), "deleted_key": a.storage_key, "deleted_at": utcnow().isoformat()}
                a.storage_key = "deleted"
                removed += 1
    return removed
