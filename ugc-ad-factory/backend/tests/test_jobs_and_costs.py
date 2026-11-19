from app.core.db import session_scope
from app.core.security import webhook_token
from app.db.models import GenerationJob, Project, ProviderRequest, UsageRecord, User
from app.pipeline import costs, dispatch, jobs
from app.providers import registry
from app.providers.base import MediaRequest, PollResult, ProviderError, SubmitResult
from app.providers.mock import MockMediaProvider


class ScriptedProvider(MockMediaProvider):
    """Mock provider with scripted submit/poll outcomes."""

    def __init__(self, submit_errors=(), poll_results=()):
        super().__init__()
        self.submit_errors = list(submit_errors)
        self.poll_results = list(poll_results)
        self.submits = 0

    def submit(self, req, *, log=lambda **k: None):
        self.submits += 1
        if self.submit_errors:
            err = self.submit_errors.pop(0)
            if err:
                raise err
        return super().submit(req, log=log)

    def poll(self, kind, pid, *, log=lambda **k: None):
        if self.poll_results:
            r = self.poll_results.pop(0)
            if r is not None:
                return r
        return super().poll(kind, pid, log=log)


def _project(budget=100000):
    with session_scope() as db:
        u = User(email="u@x.io", password_hash="x")
        db.add(u)
        db.flush()
        p = Project(owner_id=u.id, name="p", status="running", stage="video", budget_credits=budget, settings={})
        db.add(p)
        db.flush()
        return p.id


def _job(pid, key="k1", kind="image"):
    with session_scope() as db:
        req = MediaRequest(kind=kind, prompt="a person in a kitchen", duration=5)
        return jobs.create_job(db, project_id=pid, purpose="anchor", kind=kind, request=req.to_dict(),
                               idempotency_key=key).id


def _state(jid):
    with session_scope() as db:
        j = db.get(GenerationJob, jid)
        return j.status, j.attempts, j.error, j.output_asset_id


def test_create_job_is_idempotent():
    pid = _project()
    a, b = _job(pid, "same"), _job(pid, "same")
    assert a == b
    with session_scope() as db:
        assert db.query(GenerationJob).count() == 1


def test_full_lifecycle_records_usage_and_requests():
    pid = _project()
    jid = _job(pid)
    dispatch.submit_job(jid)
    dispatch.drain_inline()
    status, attempts, err, asset = _state(jid)
    assert status == "succeeded" and attempts == 1 and asset
    with session_scope() as db:
        assert db.query(UsageRecord).filter_by(job_id=jid).one().credits > 0
        ops = [r.operation for r in db.query(ProviderRequest).filter_by(job_id=jid)]
    assert "mock_submit_image" in ops and ops.count("mock_get_image") == 2  # running, then ready


def test_second_submit_is_noop_after_success():
    prov = ScriptedProvider()
    registry.override(media=prov)
    pid = _project()
    jid = _job(pid)
    jobs.submit_job(jid)
    jobs.submit_job(jid)  # compare-and-set prevents a duplicate paid request
    assert prov.submits == 1


def test_retryable_submit_error_then_success():
    prov = ScriptedProvider(submit_errors=[ProviderError("rate limited", retryable=True)])
    registry.override(media=prov)
    jid = _job(_project())
    dispatch.submit_job(jid)
    dispatch.drain_inline()
    status, attempts, _, _ = _state(jid)
    assert status == "succeeded" and attempts == 2 and prov.submits == 2


def test_non_retryable_failure_stops():
    prov = ScriptedProvider(poll_results=[PollResult(state="failed", error="not_allowed: content policy")])
    registry.override(media=prov)
    jid = _job(_project())
    dispatch.submit_job(jid)
    dispatch.drain_inline()
    status, attempts, err, _ = _state(jid)
    assert status == "failed" and attempts == 1 and "not_allowed" in err


def test_generation_failure_retries_up_to_max_attempts():
    fail = PollResult(state="failed", error="generation failed")
    prov = ScriptedProvider(poll_results=[fail, fail, fail])
    registry.override(media=prov)
    jid = _job(_project())
    dispatch.submit_job(jid)
    dispatch.drain_inline()
    status, attempts, _, _ = _state(jid)
    assert status == "failed" and attempts == 3 and prov.submits == 3


def test_success_without_url_is_not_success():
    prov = ScriptedProvider(poll_results=[PollResult(state="succeeded", output_url=None)] * 100)
    registry.override(media=prov)
    jid = _job(_project())
    dispatch.submit_job(jid)
    dispatch.drain_inline(max_steps=200)
    status, _, err, asset = _state(jid)
    assert status == "failed" and asset is None and "without an output URL" in err
    assert dispatch.pending_inline() == 0  # bounded: no endless re-polling


def test_budget_gate_pauses_project():
    pid = _project(budget=10)  # image costs 80 credits in the catalogue
    jid = _job(pid)
    dispatch.submit_job(jid)
    dispatch.drain_inline()
    with session_scope() as db:
        assert db.get(Project, pid).status == "awaiting_budget"
        assert db.get(GenerationJob, jid).status == "pending"


def test_concurrency_limit_defers(monkeypatch):
    monkeypatch.setenv("LETZAI_MAX_CONCURRENT_JOBS", "1")
    from app.core.config import reset_settings_cache
    reset_settings_cache()
    prov = ScriptedProvider()
    registry.override(media=prov)
    pid = _project()
    a, b = _job(pid, "a"), _job(pid, "b")
    jobs.submit_job(a)
    jobs.submit_job(b)  # deferred: one job already in flight
    assert prov.submits == 1 and _state(b)[0] == "pending"


def test_estimates_and_budget_check():
    media = MockMediaProvider()
    est = costs.estimate_project({"variants": 2, "duration": 20, "video_model": "video-seedance25",
                                  "resolution": "720p"}, media, has_creator=False)
    assert est["total_credits"] > 0 and est["audio_mode"] == "native"
    assert any("anchor" in l["item"] for l in est["lines"])
    est2 = costs.estimate_project({"variants": 2, "duration": 20, "video_model": "video-seedance25",
                                   "resolution": "720p"}, media, has_creator=True)
    assert est2["total_credits"] < est["total_credits"]
    pid = _project(budget=100)
    with session_scope() as db:
        p = db.get(Project, pid)
        costs.check_budget(db, p, 50)
        costs.record_usage(db, project_id=pid, job_id=None, provider="letzai", model="m", kind="video", credits=80)
        db.flush()
        try:
            costs.check_budget(db, p, 50)
            raise AssertionError("expected BudgetExceeded")
        except costs.BudgetExceeded as e:
            assert e.scope == "project"


def test_webhook_auth_and_repoll(client):
    pid = _project()
    jid = _job(pid)
    jobs.submit_job(jid)
    dispatch.clear_inline()
    assert client.post(f"/api/webhooks/letzai/{jid}?token=wrong", json={}).status_code == 403
    r = client.post(f"/api/webhooks/letzai/{jid}?token={webhook_token(jid)}",
                    json={"status": "ready", "videoVersions": {"original": "https://evil.example/x.mp4"}})
    assert r.status_code == 202 and dispatch.pending_inline() == 1  # re-poll queued, payload ignored
    dispatch.drain_inline()
    with session_scope() as db:
        assert not (db.get(GenerationJob, jid).output_url or "").startswith("https://evil")
