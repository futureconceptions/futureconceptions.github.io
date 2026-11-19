from app.agents import audio_director, lipsync_specialist
from app.agents import prompts as P
from app.agents.creator_director import CreatorDirector, anchor_prompt
from app.agents.researcher import ProductResearcher, extract_page, heuristic_research
from app.agents.scene_director import SceneDirector, compose_prompts, fit_to_model
from app.agents.schemas import Beat, ConceptDraft, ProductResearch, SceneSpec, SupportedClaim
from app.agents.strategist import AdvertisingStrategist, select_concepts, validate_concept
from app.providers.base import VideoModelInfo
from app.providers.llm import HeuristicLLM

HTML = """<html><head><title>AquaBottle 750 | Aqua Shop</title>
<meta name="description" content="Insulated steel bottle that keeps drinks cold for 24 hours.">
<meta property="og:title" content="AquaBottle 750">
<script type="application/ld+json">{"@type":"Product","name":"AquaBottle 750","brand":"Aqua",
 "offers":{"price":"29.90","priceCurrency":"EUR"}}</script><script>var tracking=1;</script></head>
<body><nav>Home Shop Cart</nav><h1>AquaBottle 750</h1>
<p>Keeps drinks cold for 24 hours and hot for 12 hours.</p>
<ul><li>Made from 18/8 stainless steel</li><li>Leak-proof lid for your bag</li></ul>
<footer>Imprint and privacy policy</footer></body></html>"""


def info(min_d=4, max_d=15, audio=True):
    return VideoModelInfo(key="video-x", display_name="X", min_duration=min_d, max_duration=max_d,
                          resolutions=["720p"], aspect_ratios=["9:16"], native_audio=audio, always_audio=audio,
                          supports_reference=True, supports_text_to_video=True, max_reference_images=9, active=True)


def research(**kw):
    base = dict(product_name="AquaBottle", brand="Aqua", category="drinkware", summary="Steel bottle",
                features=["24h cold"], benefits=["cold drinks"], target_audience=["commuters"],
                customer_problems=["warm water by noon"], differentiators=[],
                supported_claims=[SupportedClaim(claim="Keeps drinks cold for 24 hours", evidence="Keeps drinks cold for 24 hours", source="product_page"),
                                  SupportedClaim(claim="Leak-proof lid", evidence="Leak-proof lid for your bag", source="product_page")],
                claims_to_avoid=[], potential_objections=["price"], before_after_supported=False)
    base.update(kw)
    return ProductResearch(**base)


# ---------------------------------------------------------------- research
def test_extract_page_keeps_content_drops_chrome():
    page = extract_page(HTML)
    assert page.title.startswith("AquaBottle 750")
    assert page.meta["jsonld_product"][0]["name"] == "AquaBottle 750"
    assert "Keeps drinks cold for 24 hours" in page.text
    assert "tracking" not in page.text and "Imprint" not in page.text


def test_heuristic_research_only_uses_verbatim_source_sentences():
    page = extract_page(HTML)
    r = heuristic_research(None, "Aqua", "The lid is leak-proof. It weighs 350 grams.", page, None, "en")
    sources = "The lid is leak-proof. It weighs 350 grams. " + page.text
    assert r.supported_claims and all(c.claim in sources for c in r.supported_claims)
    assert r.before_after_supported is False


def test_researcher_skips_page_when_robots_disallows(monkeypatch):
    from app.agents import researcher as R
    monkeypatch.setattr(R, "robots_allows", lambda url: False)
    r, page, _ = ProductResearcher(HeuristicLLM()).run(url="https://shop.example.com/p", name="X", brand=None,
                                                       description="X keeps tea warm.", audience=None, language="en")
    assert page.status == "robots_disallowed" and r.supported_claims[0].claim == "X keeps tea warm."


# ---------------------------------------------------------------- strategy
def test_fabricated_experience_is_rejected():
    assert P.fabricated_experience_flags("I've been using this for 3 months and it changed my life")
    assert P.fabricated_experience_flags("Ich benutze es seit Wochen")
    assert not P.fabricated_experience_flags("Look how the lid seals - no leaks in your bag.")


def _draft(angle="product_demo", dialogue="Look at this bottle. Keeps drinks cold for 24 hours.", **kw):
    d = dict(angle=angle, title="t", hook="h", core_message="m", emotional_angle="e", visual_concept="v",
             cta="Shop now", target_duration=10, beats=[Beat(beat="hook", dialogue=dialogue, on_screen_action="a", seconds=10)],
             claims_used=["Keeps drinks cold for 24 hours"], self_score=8, rationale="r")
    d.update(kw)
    return ConceptDraft(**d)


def test_validation_rules():
    r = research()
    assert validate_concept(_draft(), r, "en").valid
    assert not validate_concept(_draft(angle="before_after"), r, "en").valid
    assert validate_concept(_draft(angle="before_after"), research(before_after_supported=True), "en").valid
    assert not validate_concept(_draft(dialogue="My results were amazing"), r, "en").valid
    v = validate_concept(_draft(claims_used=["Cures headaches"]), r, "en")
    assert any("unverified" in p for p in v.problems) and v.score < 8
    long = validate_concept(_draft(dialogue=" ".join(["word"] * 60)), r, "en")
    assert any("word budget" in p for p in long.problems)


def test_selection_prefers_distinct_angles():
    r = research()
    vs = [validate_concept(_draft(angle=a, self_score=s), r, "en")
          for a, s in [("product_demo", 9), ("product_demo", 8.9), ("educational", 7), ("problem_solution", 6)]]
    chosen = select_concepts(vs, 3)
    assert [c.draft.angle for c in chosen] == ["product_demo", "educational", "problem_solution"]


def test_strategist_heuristic_german_scripts_fit_budget():
    validated, selected, _ = AdvertisingStrategist(HeuristicLLM()).run(
        research(), language="de", duration=15, variants=2, cta="Jetzt ansehen", audience=None, brand_guidelines=None)
    assert len(selected) == 2 and len({s.draft.angle for s in selected}) == 2
    for s in selected:
        words = sum(len(b.dialogue.split()) for b in s.draft.beats)
        assert words <= P.max_words(15, "de") * 1.15
        assert s.draft.beats[-1].dialogue == "Jetzt ansehen"
        assert abs(sum(b.seconds for b in s.draft.beats) - 15) < 1.5


# ---------------------------------------------------------------- creator & scenes
def test_creator_anchor_prompt_is_realistic_and_fictional():
    spec, _ = CreatorDirector(HeuristicLLM()).design(research(), {"gender": "male"}, "en")
    p = anchor_prompt(spec)
    assert "fictional" in p and "unretouched skin" in p and "No on-screen text" in p
    assert not any(w in p.lower().split() for w in ("masterpiece", "stunning", "8k"))


def test_fit_to_model_merges_and_splits():
    mk = lambda d, t="hi there": SceneSpec(beat="b", duration=d, dialogue=t, framing="f", creator_movement="m",
                                           product_interaction="none", environment="e", needs_product_reference=False,
                                           keyframe_prompt="k", video_prompt="v", audio_requirements="a")
    out = fit_to_model([mk(2), mk(5), mk(25, " ".join(["w"] * 40))], info(4, 10), "en")
    assert out[0].duration == 7 and "hi there hi there" == out[0].dialogue
    assert all(4 <= s.duration <= 10 for s in out)
    assert sum(len(s.dialogue.split()) for s in out[1:]) == 40


def test_compose_prompts_contains_locks():
    sp = SceneSpec(beat="hook", duration=5, dialogue="Look at this.", framing="close-up", creator_movement="holds bottle",
                   product_interaction="holds bottle", environment="kitchen", needs_product_reference=True,
                   keyframe_prompt="holding bottle, stunning", video_prompt="lifts bottle", audio_requirements="")
    kf, vp = compose_prompts(sp, {"lighting": "window light"}, "de", "native")
    assert "IDENTITY REFERENCE" in kf and "product reference image exactly" in kf and "stunning" not in kf
    assert '"Look at this."' in vp and "German" in vp
    _, vo = compose_prompts(sp, {}, "en", "tts")
    assert "do not speak" in vo


def test_scene_director_heuristic_respects_limits():
    beats = [Beat(beat="hook", dialogue="Quick one.", on_screen_action="a", seconds=2.5),
             Beat(beat="demo", dialogue="It keeps drinks cold for a whole day.", on_screen_action="b", seconds=8),
             Beat(beat="cta", dialogue="Check it out.", on_screen_action="c", seconds=2.5)]
    scenes, _, _ = SceneDirector(HeuristicLLM()).plan(beats=beats, concept_title="t", creator={}, product_name="P",
                                                      has_product_images=True, info=info(5, 10), language="en",
                                                      audio_mode="native")
    assert all(5 <= s.duration <= 10 for s in scenes)
    assert " ".join(s.dialogue for s in scenes).split() == "Quick one. It keeps drinks cold for a whole day. Check it out.".split()


# ---------------------------------------------------------------- audio & lip-sync decisions
def test_audio_mode_and_speech_normalisation():
    assert audio_director.choose_audio_mode(info(audio=True), None) == "native"
    assert audio_director.choose_audio_mode(info(audio=False), "native") == "tts"
    assert audio_director.prepare_speech_text("Nur 3 Tage, 20% günstiger", "de") == "Nur drei Tage, zwanzig Prozent günstiger"


def test_lipsync_decisions():
    d = lipsync_specialist.decide
    assert d(audio_source="native", has_dialogue=True, clip_has_audio=True, lipsync_available=False) == "native"
    assert d(audio_source="tts", has_dialogue=True, clip_has_audio=False, lipsync_available=True) == "sync"
    assert d(audio_source="tts", has_dialogue=True, clip_has_audio=False, lipsync_available=False) == "voiceover"
    assert d(audio_source="none", has_dialogue=False, clip_has_audio=False, lipsync_available=True) == "none"
