"""Test configuration: SQLite + local storage + inline task dispatch + mock
providers. No test consumes paid API credits (the opt-in integration test in
test_integration_letzai.py is skipped unless explicitly enabled)."""
from __future__ import annotations

import os
import shutil
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="ugc-tests-")
os.environ.update({
    "APP_ENV": "test",
    "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
    "STORAGE_BACKEND": "local",
    "LOCAL_STORAGE_DIR": f"{_TMP}/storage",
    "UGC_MOCK_DIR": f"{_TMP}/mock",
    "UGC_TMP": f"{_TMP}/tmp",
    "TASK_DISPATCH": "inline",
    "MEDIA_PROVIDER": "mock",
    "LLM_PROVIDER": "heuristic",
    "LIPSYNC_PROVIDER": "none",
    "POLL_INTERVAL_SECONDS": "0",
    "PUBLIC_API_URL": "http://testserver",
    "BOOTSTRAP_ADMIN_EMAIL": "admin@example.com",
    "BOOTSTRAP_ADMIN_PASSWORD": "admin12345",
    "SECRET_KEY": "test-secret-key-test-secret-key-0123456789",
    "LETZAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
})

from app.core.config import reset_settings_cache  # noqa: E402
from app.core.db import Base, get_engine, reset_engine  # noqa: E402
from app.db import models as _models  # noqa: E402,F401  (register tables)
from app.pipeline import dispatch  # noqa: E402
from app.providers import registry  # noqa: E402
from app.services import storage  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_state(monkeypatch):
    reset_settings_cache()
    reset_engine()
    storage.set_storage(None)
    registry.clear_overrides()
    dispatch.clear_inline()
    db_path = f"{_TMP}/test.db"
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(db_path + suffix):
            os.remove(db_path + suffix)
    Base.metadata.create_all(get_engine())
    yield
    dispatch.clear_inline()
    registry.clear_overrides()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin12345"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def product_image(tmp_path):
    from app.media import ffmpeg as ff
    p = tmp_path / "product.png"
    ff.make_still(str(p), 600, 600, color="0x3355cc")
    return str(p)


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)
