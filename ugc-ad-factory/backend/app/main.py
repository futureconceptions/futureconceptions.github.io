from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from app.api.routers import creators, misc, projects
from app.core.config import get_settings
from app.core.db import get_engine, session_scope
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.models import User
from app.services.storage import get_storage

log = get_logger("api")


def bootstrap() -> None:
    s = get_settings()
    try:
        get_storage().ensure_ready()
    except Exception as e:  # noqa: BLE001
        log.warning("storage_not_ready", error=str(e))
    if s.bootstrap_admin_email and s.bootstrap_admin_password:
        with session_scope() as db:
            if not db.scalar(select(User).limit(1)):
                db.add(User(email=s.bootstrap_admin_email.lower(), role="admin", full_name="Administrator",
                            password_hash=hash_password(s.bootstrap_admin_password.get_secret_value())))
                log.info("bootstrap_admin_created", email=s.bootstrap_admin_email)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    s = get_settings()
    if s.app_env == "production" and "change-me" in s.secret_key.get_secret_value():
        raise RuntimeError("SECRET_KEY must be set in production")
    bootstrap()
    yield


app = FastAPI(title="UGC Ad Factory API", version="1.0.0", lifespan=lifespan,
              description="Autonomous UGC advertisement production on LetzAI. "
                          "All endpoints except /api/auth/login, /api/health, signed /api/files and "
                          "token-authenticated webhooks require a Bearer token.")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    structlog.contextvars.bind_contextvars(request_id=rid)
    t0 = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as e:  # noqa: BLE001
        log.error("unhandled_error", path=request.url.path, error=str(e))
        response = JSONResponse({"detail": "Internal server error", "request_id": rid}, status_code=500)
    response.headers["x-request-id"] = rid
    if not request.url.path.startswith("/api/files"):
        log.info("request", method=request.method, path=request.url.path, status=response.status_code,
                 ms=int((time.monotonic() - t0) * 1000))
    structlog.contextvars.clear_contextvars()
    return response


@app.get("/api/health", tags=["core"])
def health():
    checks = {}
    try:
        with get_engine().connect() as c:
            c.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:  # noqa: BLE001
        checks["database"] = f"error: {e.__class__.__name__}"
    s = get_settings()
    if s.task_dispatch == "celery":
        try:
            import redis
            redis.Redis.from_url(s.redis_url, socket_timeout=2).ping()
            checks["redis"] = "ok"
        except Exception as e:  # noqa: BLE001
            checks["redis"] = f"error: {e.__class__.__name__}"
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse({"status": "ok" if ok else "degraded", "checks": checks,
                         "media_provider": s.media_provider}, status_code=200 if ok else 503)


app.include_router(misc.router)
app.include_router(projects.router)
app.include_router(creators.router)
