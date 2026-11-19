"""Task dispatch abstraction: Celery in deployments, an in-process queue for
tests and single-process development. Pipeline code only calls these."""
from __future__ import annotations

import heapq
import itertools
import time
from typing import Callable

from app.core.config import get_settings

_inline_queue: list[tuple[float, int, str, str]] = []
_counter = itertools.count()


def advance_project(project_id: str, delay: float = 0) -> None:
    _send("advance_project", project_id, delay)


def poll_job(job_id: str, delay: float = 0) -> None:
    _send("poll_job", job_id, delay)


def submit_job(job_id: str, delay: float = 0) -> None:
    _send("submit_job", job_id, delay)


def _send(task: str, arg: str, delay: float) -> None:
    if get_settings().task_dispatch == "inline":
        heapq.heappush(_inline_queue, (time.monotonic() + delay, next(_counter), task, arg))
        return
    from app.worker import tasks
    getattr(tasks, task).apply_async(args=[arg], countdown=max(0, delay))


def drain_inline(max_steps: int = 2000, *, ignore_delays: bool = True,
                 on_step: Callable[[str, str], None] | None = None) -> int:
    """Run queued inline tasks until the queue is empty. Delays are skipped
    (ignore_delays) so tests do not sleep. Returns the number of tasks run."""
    from app.pipeline import runner
    steps = 0
    while _inline_queue and steps < max_steps:
        due, _, task, arg = heapq.heappop(_inline_queue)
        if not ignore_delays and due > time.monotonic():
            time.sleep(due - time.monotonic())
        if on_step:
            on_step(task, arg)
        getattr(runner, task)(arg)
        steps += 1
    return steps


def clear_inline() -> None:
    _inline_queue.clear()


def pending_inline() -> int:
    return len(_inline_queue)
