import json

import httpx
import pytest
import respx
from pydantic import ValidationError

from app.providers.base import MediaRequest, ProviderError
from app.providers.letzai import schemas as S
from app.providers.letzai.adapter import LetzAIProvider, clamp_duration, size_for
from app.providers.letzai.catalog import load_snapshot
from app.providers.letzai.client import LetzAIClient

BASE = "https://api.letz.ai"


def make_client(**kw):
    return LetzAIClient("test-key", BASE, sleep=lambda s: None, **kw)


def make_provider(client):
    p = LetzAIProvider.__new__(LetzAIProvider)
    p.client = client
    p.org = None
    from app.providers.letzai.catalog import CatalogCache
    p.catalog = CatalogCache(None)
    return p


# ------------------------------------------------------------------ schema validation
def test_image_request_rejects_unknown_fields_and_ranges():
    with pytest.raises(ValidationError):
        S.ImageCreateRequest(prompt="x", aspectRatio="9:16")  # not a field on POST /images
    with pytest.raises(ValidationError):
        S.ImageCreateRequest(prompt="x", width=4000)
    with pytest.raises(ValidationError):
        S.ImageCreateRequest(prompt="")
    body = S.ImageCreateRequest(prompt="a", width=1080, height=1920).body()
    assert "organizationId" not in body and body["width"] == 1080


def test_image_edit_limits_and_audio_validation():
    with pytest.raises(ValidationError):
        S.ImageEditRequest(prompt="x", inputImageUrls=[f"https://x/{i}.png" for i in range(10)])
    with pytest.raises(ValidationError):
        S.AudioCreateRequest(kind="speech", baseModel="audio-eleven-v4")  # speech needs text
    S.AudioCreateRequest(kind="speech", baseModel="audio-eleven-v4", text="Hallo")


# ------------------------------------------------------------------ client behaviour
@respx.mock
def test_create_image_sends_bearer_and_typed_response():
    route = respx.post(f"{BASE}/images").mock(return_value=httpx.Response(201, json={
        "id": "img-1", "status": "new", "progress": 0, "prompt": "p"}))
    c = make_client()
    r = c.create_image(S.ImageCreateRequest(prompt="p", width=1080, height=1920, baseModel="gemini-3-pro-image"))
    assert r.id == "img-1"
    req = route.calls.last.request
    assert req.headers["authorization"] == "Bearer test-key"
    assert json.loads(req.content)["baseModel"] == "gemini-3-pro-image"


@respx.mock
def test_retries_on_429_then_succeeds_and_logs_every_call():
    route = respx.get(f"{BASE}/videos/v1").mock(side_effect=[
        httpx.Response(429, json={"message": "slow down"}, headers={"retry-after": "1"}),
        httpx.Response(503, json={"message": "busy"}),
        httpx.Response(200, json={"id": "v1", "status": "generating", "progress": 40})])
    calls = []
    r = make_client().get_video("v1", log=lambda **kw: calls.append(kw))
    assert r.status == "generating" and route.call_count == 3
    assert [c["status_code"] for c in calls] == [429, 503, 200]


@respx.mock
def test_validation_error_is_not_retried():
    route = respx.post(f"{BASE}/videos").mock(return_value=httpx.Response(400, json={"message": ["duration must be <= 30"]}))
    with pytest.raises(ProviderError) as e:
        make_client().create_video(S.VideoCreateRequest(prompt="x", settings=S.VideoSettings(mode="video-kling4")))
    assert route.call_count == 1 and not e.value.retryable and "duration" in str(e.value)


@respx.mock
def test_retries_exhausted_marks_retryable():
    respx.get(f"{BASE}/audios/a1").mock(return_value=httpx.Response(502, text="bad gateway"))
    with pytest.raises(ProviderError) as e:
        make_client(max_retries=2).get_audio("a1")
    assert e.value.retryable


@respx.mock
def test_upload_is_two_step_and_put_has_no_auth():
    respx.post(f"{BASE}/user-assets").mock(return_value=httpx.Response(201, json={
        "id": "ua1", "imageUrl": "https://cdn.letz.ai/u/a.png", "uploadUrl": "https://s3.example.com/up?sig=1",
        "userId": "u", "createdAt": "x", "updatedAt": "x"}))
    put = respx.put("https://s3.example.com/up?sig=1").mock(return_value=httpx.Response(200))
    asset = make_client().upload_file(b"\x89PNG", "png", "image/png", "a.png")
    assert asset.imageUrl.endswith("a.png")
    assert "authorization" not in put.calls.last.request.headers
    assert put.calls.last.request.headers["content-type"] == "image/png"


# ------------------------------------------------------------------ adapter mapping & normalisation
@respx.mock
def test_video_request_mapping_respects_model_limits():
    route = respx.post(f"{BASE}/videos").mock(return_value=httpx.Response(201, json={"id": "v9", "status": "new"}))
    prov = make_provider(make_client())
    req = MediaRequest(kind="video", prompt="talk", model="seedance25", duration=45,
                       image_urls=["https://cdn/key.png", "https://cdn/product.png"], resolution="720p",
                       with_audio=True)
    res = prov.submit(req)
    body = json.loads(route.calls.last.request.content)
    assert res.provider_job_id == "v9"
    assert body["settings"]["mode"] == "video-seedance25"
    assert body["settings"]["duration"] == 30  # clamped to the model maximum
    assert body["settings"]["withSound"] is True  # always-audio model
    assert body["imageUrl"] == "https://cdn/key.png"
    assert body["assetUrls"] == ["https://cdn/product.png"]
    assert (body["width"], body["height"]) == (720, 1280)


@respx.mock
def test_image_with_references_routes_to_image_edits():
    route = respx.post(f"{BASE}/image-edits").mock(return_value=httpx.Response(201, json={"id": "e1", "status": "new"}))
    prov = make_provider(make_client())
    prov.submit(MediaRequest(kind="image", prompt="same person", image_urls=["https://cdn/a.png"]))
    body = json.loads(route.calls.last.request.content)
    assert body["mode"] == "context" and body["inputImageUrls"] == ["https://cdn/a.png"]
    assert body["settings"]["aspect_ratio"] == "9:16"


@respx.mock
@pytest.mark.parametrize("payload,state", [
    ({"id": "v", "status": "ready", "videoVersions": {"original": "https://cdn/v.mp4"}}, "succeeded"),
    ({"id": "v", "status": "saved", "videoVersions": {"original": "https://cdn/v.mp4"}}, "succeeded"),
    ({"id": "v", "status": "ready", "videoVersions": {}}, "failed"),  # never assume success
    ({"id": "v", "status": "generating", "progress": 30}, "running"),
    ({"id": "v", "status": "new"}, "running"),
    ({"id": "v", "status": "failed", "statusDetail": "provider error"}, "failed"),
    ({"id": "v", "status": "interrupted"}, "failed"),
])
def test_video_status_normalisation(payload, state):
    respx.get(f"{BASE}/videos/v").mock(return_value=httpx.Response(200, json=payload))
    assert make_provider(make_client()).poll("video", "v").state == state


@respx.mock
def test_image_edit_result_read_from_generated_completion():
    respx.get(f"{BASE}/image-edits/e").mock(return_value=httpx.Response(200, json={
        "id": "e", "status": "ready", "generatedImageCompletion": {"imageVersions": {"original": "https://cdn/e.png"}}}))
    r = make_provider(make_client()).poll("image_edit", "e")
    assert r.state == "succeeded" and r.output_url == "https://cdn/e.png"


@respx.mock
def test_speech_request_and_credits():
    route = respx.post(f"{BASE}/audios").mock(return_value=httpx.Response(201, json={"id": "a", "status": "new"}))
    respx.get(f"{BASE}/audios/a").mock(return_value=httpx.Response(200, json={
        "id": "a", "status": "ready", "audioUrl": "https://cdn/a.mp3", "credits": 12, "durationSeconds": 3.1}))
    prov = make_provider(make_client())
    prov.submit(MediaRequest(kind="speech", text="Hallo zusammen", voice="friendly-young", language="de"))
    body = json.loads(route.calls.last.request.content)
    assert body["kind"] == "speech" and body["settings"] == {"voice": "friendly-young", "language": "de"}
    r = prov.poll("speech", "a")
    assert r.credits == 12 and r.output_url.endswith("a.mp3")


# ------------------------------------------------------------------ catalogue
def test_catalog_aliases_limits_and_pricing():
    cat = load_snapshot()
    assert cat.resolve("kling4") == "video-kling4"
    info = cat.video_model("seedance-2.5")
    assert (info.min_duration, info.max_duration) == (4, 30) and info.always_audio
    assert clamp_duration(2, info) == 4 and clamp_duration(99, info) == 30
    assert cat.price_video("video-seedance25", 10, "720p", True) == 3000
    assert cat.price_image("gemini-3-pro-image") == 80
    assert cat.image_api_mode("gemini-3-pro-image", "hd") == "2k"
    assert "friendly-young" in cat.speech_voices("audio-eleven-v4")
    with pytest.raises(KeyError):
        cat.video_model("not-a-model")


def test_size_for_portrait():
    assert size_for("1080p") == (1080, 1920)
    assert size_for("720p", "16:9") == (1280, 720)


def test_catalog_cache_falls_back_to_snapshot():
    from app.providers.letzai.catalog import CatalogCache

    def boom():
        raise RuntimeError("offline")
    cache = CatalogCache(boom)
    assert cache.get().resolve("kling4") and cache.source == "snapshot"
