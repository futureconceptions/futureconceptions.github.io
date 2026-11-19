from __future__ import annotations

from celery import Celery

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
_s = get_settings()

celery_app = Celery("ugc", broker=_s.redis_url, backend=_s.redis_url, include=["app.worker.tasks"])
celery_app.conf.update(
    task_acks_late=True,               # a crashed worker's task is redelivered
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_queue="pipeline",
    task_routes={"app.worker.tasks.poll_job": {"queue": "polling"},
                 "app.worker.tasks.submit_job": {"queue": "polling"}},
    task_time_limit=60 * 30,
    task_soft_time_limit=60 * 25,
    broker_transport_options={"visibility_timeout": 60 * 60},
    beat_schedule={"recover-stale": {"task": "app.worker.tasks.recover_stale", "schedule": 60.0},
                   "retention": {"task": "app.worker.tasks.apply_retention", "schedule": 6 * 3600.0}},
    timezone="UTC",
)
