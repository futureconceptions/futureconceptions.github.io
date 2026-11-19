"""OPT-IN live test against the real LetzAI API. It spends real credits
(one low-cost image, ~10 credits at list price) and is skipped unless BOTH are set:

    LETZAI_API_KEY=...               your key
    LETZAI_LIVE_TEST=I_ACCEPT_COSTS  explicit approval

Run:  LETZAI_LIVE_TEST=I_ACCEPT_COSTS LETZAI_API_KEY=... pytest tests/test_integration_letzai.py -s
"""
import os
import tempfile
import time

import pytest

LIVE = os.environ.get("LETZAI_LIVE_TEST") == "I_ACCEPT_COSTS"
KEY = os.environ.get("LIVE_LETZAI_API_KEY") or os.environ.get("LETZAI_API_KEY_LIVE")

pytestmark = pytest.mark.skipif(not (LIVE and KEY),
                                reason="live LetzAI test disabled (set LETZAI_LIVE_TEST=I_ACCEPT_COSTS and LIVE_LETZAI_API_KEY)")

MODEL = os.environ.get("LETZAI_LIVE_MODEL", "mai-image-2-7-flash")


def test_one_real_image_generation():
    from app.media import ffmpeg as ff
    from app.providers.base import MediaRequest
    from app.providers.letzai.adapter import LetzAIProvider
    from app.providers.letzai.client import LetzAIClient

    prov = LetzAIProvider(LetzAIClient(KEY))
    req = MediaRequest(kind="image", model=MODEL, width=720, height=1280,
                       prompt="Vertical phone photo of a ceramic coffee mug on a wooden kitchen counter, window light")
    try:
        print("quote (credits):", prov.quote(req))
    except Exception as e:  # quote is informative only
        print("quote unavailable:", e)
    sub = prov.submit(req)
    assert sub.provider_job_id
    deadline = time.time() + 300
    while time.time() < deadline:
        r = prov.poll("image", sub.provider_job_id)
        if r.state != "running":
            break
        time.sleep(3)
    assert r.state == "succeeded", r.error
    with tempfile.TemporaryDirectory() as td:
        path = prov.download(r.output_url, os.path.join(td, "out.png"))
        info = ff.probe(path)
        assert info.width and info.height
        print("generated", r.output_url, info.width, info.height)
