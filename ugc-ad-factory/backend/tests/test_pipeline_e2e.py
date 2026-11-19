"""End-to-end through the HTTP API with mock providers: product in -> finished
MP4 advertisements + QA reports out. Real FFmpeg runs; no paid APIs."""
import json

from app.agents.schemas import QAIssue, SceneVisualQA
from app.core.db import session_scope
from app.db.models import GenerationJob, Project, Scene
from app.pipeline import dispatch
from app.providers import registry
from app.providers.base import LLMUsage
from app.providers.llm import HeuristicLLM


def create(client, auth, product_image=None, **overrides):
    payload = {"name": "AquaBottle", "brand_name": "Aqua", "language": "en", "duration": 10, "variants": 1,
               "product_description": "AquaBottle keeps drinks cold for 24 hours. It is made of stainless steel. "
                                      "The lid is leak-proof.",
               "cta": "Get yours today", "video_model": "video-seedance25", "resolution": "480p",
               "assets_licensed": bool(product_image)}
    payload.update(overrides)
    files = [("images", ("product.png", open(product_image, "rb"), "image/png"))] if product_image else []
    r = client.post("/api/projects", headers=auth, data={"payload": json.dumps(payload)}, files=files)
    assert r.status_code == 201, r.text
    return r.json()


def detail(client, auth, pid):
    return client.get(f"/api/projects/{pid}", headers=auth).json()


def test_product_to_finished_ads(client, auth, product_image):
    out = create(client, auth, product_image, variants=2, language="de", cta="Jetzt ausprobieren")
    assert out["estimate"]["total_credits"] > 0
    pid = out["project"]["id"]
    dispatch.drain_inline()
    d = detail(client, auth, pid)
    assert d["status"] == "completed", (d["error"], d["stage_detail"])
    assert all(s["state"] == "done" for s in d["pipeline"])
    assert len([c for c in d["concepts"] if c["selected"]]) == 2
    assert d["creator"]["anchor_url"] and d["creator"]["is_fictional"]
    exports = [e for e in d["exports"] if e["status"] == "approved"]
    assert len(exports) == 2
    for e in exports:
        assert (e["width"], e["height"]) == (1080, 1920)
        video = client.get(e["video_url"].replace("http://testserver", ""))
        assert video.status_code == 200 and video.content[4:8] == b"ftyp"
        assert e["qa"]["passed"]
    # every external generation is tracked with provider job ids and costs
    assert all(j["provider_job_id"] and j["status"] == "succeeded" for j in d["jobs"])
    assert sum(u["credits"] for u in d["usage"]) > 0
    dash = client.get("/api/dashboard", headers=auth).json()
    assert dash["total_ads"] == 2 and dash["completed_videos"] == 2 and dash["active_jobs"] == 0
    lib = client.get("/api/exports", headers=auth).json()
    assert len(lib) == 2 and lib[0]["project"]["id"] == pid
    ex = client.get(f"/api/exports/{lib[0]['id']}", headers=auth).json()
    assert ex["concept_detail"]["script"]["full_text"] and ex["versions"]


def test_requires_some_product_input(client, auth):
    r = client.post("/api/projects", headers=auth, data={"payload": json.dumps({"language": "en"})})
    assert r.status_code == 422


def test_images_require_rights_confirmation(client, auth, product_image):
    payload = {"product_description": "x", "assets_licensed": False}
    r = client.post("/api/projects", headers=auth, data={"payload": json.dumps(payload)},
                    files=[("images", ("p.png", open(product_image, "rb"), "image/png"))])
    assert r.status_code == 422


def test_approval_checkpoints(client, auth):
    pid = create(client, auth, approval_checkpoints=["concepts", "creator"])["project"]["id"]
    dispatch.drain_inline()
    d = detail(client, auth, pid)
    assert d["status"] == "awaiting_approval" and d["stage"] == "script"
    other = [c for c in d["concepts"] if not c["selected"]][0]
    client.post(f"/api/projects/{pid}/approve", headers=auth,
                json={"checkpoint": "concepts", "selected_concept_ids": [other["id"]]})
    dispatch.drain_inline()
    d = detail(client, auth, pid)
    assert d["status"] == "awaiting_approval" and d["stage"] == "character"
    assert [c["id"] for c in d["concepts"] if c["selected"]] == [other["id"]]
    client.post(f"/api/projects/{pid}/approve", headers=auth, json={"checkpoint": "creator"})
    dispatch.drain_inline()
    d = detail(client, auth, pid)
    assert d["status"] == "completed" and d["creator"]["status"] == "approved"


def test_budget_confirmation_required(client, auth):
    out = create(client, auth, budget_credits=100)
    assert out["project"]["status"] == "awaiting_budget"
    pid = out["project"]["id"]
    dispatch.drain_inline()
    assert detail(client, auth, pid)["stage"] == "research"  # nothing ran
    client.post(f"/api/projects/{pid}/confirm-budget", headers=auth, json={})
    dispatch.drain_inline()
    assert detail(client, auth, pid)["status"] == "completed"


class FlakyVision(HeuristicLLM):
    """Vision QA that fails identity on round 0 and passes after regeneration."""
    supports_vision = True

    def structured(self, *, system, prompt, schema, images=None, task="", fallback=None):
        if task != "scene_qa":
            return super().structured(system=system, prompt=prompt, schema=schema, images=images, task=task,
                                      fallback=fallback)
        with session_scope() as db:
            regen = db.query(Scene).filter(Scene.regen_round > 0).count()
        score = 0.9 if regen else 0.3
        return SceneVisualQA(identity_match=score > 0.8, identity_score=score, product_accuracy="ok",
                             invented_branding=False, hand_anatomy_ok=True, visual_artifacts=False, continuity_ok=True,
                             issues=[] if regen else [QAIssue(check="identity", severity="high", detail="face drift")],
                             overall_score=score), LLMUsage(model="fake")


def test_qa_regenerates_only_failed_scenes(client, auth, product_image):
    registry.override(llm=FlakyVision())
    pid = create(client, auth, product_image)["project"]["id"]
    dispatch.drain_inline()
    d = detail(client, auth, pid)
    assert d["status"] == "completed" and d["qa_round"] == 1
    scene_reports = [r for r in d["qa_reports"] if r["scope"] == "scene"]
    assert any(not r["passed"] for r in scene_reports) and any(r["passed"] and r["round"] == 1 for r in scene_reports)
    with session_scope() as db:
        rounds = {j.round for j in db.query(GenerationJob).filter_by(purpose="scene_video")}
        n_scenes = db.query(Scene).count()
        assert rounds == {0, 1}
        assert db.query(GenerationJob).filter_by(purpose="scene_video").count() == 2 * n_scenes
    assert [e["version"] for e in d["exports"]] == [1, 2]
    assert d["exports"][-1]["status"] == "approved" and d["exports"][0]["status"] == "superseded"


def test_failed_generation_fails_project_and_retry_resumes(client, auth, monkeypatch):
    from app.providers.mock import MockMediaProvider
    registry.override(media=MockMediaProvider(fail_prompts_containing="Continue from this exact source image"))
    pid = create(client, auth)["project"]["id"]
    dispatch.drain_inline()
    d = detail(client, auth, pid)
    assert d["status"] == "failed" and d["stage"] == "video"
    assert any(j["status"] == "failed" and j["attempts"] == 3 for j in d["jobs"])
    registry.override(media=MockMediaProvider())
    assert client.post(f"/api/projects/{pid}/retry", headers=auth).status_code == 200
    dispatch.drain_inline()
    assert detail(client, auth, pid)["status"] == "completed"


def test_cancel_stops_project(client, auth):
    pid = create(client, auth)["project"]["id"]
    r = client.post(f"/api/projects/{pid}/cancel", headers=auth)
    assert r.json()["status"] == "cancelled"
    dispatch.drain_inline()
    with session_scope() as db:
        assert db.get(Project, pid).status == "cancelled"


def test_creator_library_and_reuse(client, auth, product_image):
    r = client.post("/api/creators", headers=auth, json={"name": "Mia", "appearance": {"hair": "short red hair"},
                                                         "voice_preset": "bright-host"})
    assert r.status_code == 201
    cid = r.json()["id"]
    dispatch.drain_inline()
    c = client.get(f"/api/creators/{cid}", headers=auth).json()
    assert c["status"] == "ready" and c["anchor_url"] and c["references"][0]["kind"] == "anchor"
    anchor_before = c["anchor_url"].split("?")[0]
    out = create(client, auth, creator_id=cid)
    dispatch.drain_inline()
    d = detail(client, auth, out["project"]["id"])
    assert d["status"] == "completed" and d["creator"]["id"] == cid
    assert d["creator"]["anchor_url"].split("?")[0] == anchor_before  # same identity reused
    assert not [j for j in d["jobs"] if j["purpose"] == "anchor"]
    # real-person likeness requires consent
    bad = client.post("/api/creators", headers=auth, json={"name": "Real", "is_fictional": False})
    assert bad.status_code == 422
