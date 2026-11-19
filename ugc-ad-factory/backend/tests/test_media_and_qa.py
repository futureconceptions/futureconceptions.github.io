import os

import pytest

from app.agents.editor import EditSettings, SceneClip, VideoEditor
from app.agents.qa import QualityAssurance
from app.agents.schemas import QAIssue, SceneVisualQA
from app.media import ffmpeg as ff
from app.providers.base import LLMUsage
from app.providers.llm import HeuristicLLM
from app.providers.transcription import NoTranscription, dialogue_similarity


@pytest.fixture
def speech_clip(tmp_path):
    """3s still clip: 1.5s tone ('speech') then 1.5s silence."""
    img = ff.make_still(str(tmp_path / "s.png"), 360, 640)
    tone = tmp_path / "tone.wav"
    ff.run(["-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=1.5", "-f", "lavfi", "-i",
            "anullsrc=r=48000:cl=mono", "-filter_complex", "[0][1]concat=n=2:v=0:a=1,atrim=0:3[a]", "-map", "[a]",
            str(tone)])
    out = tmp_path / "clip.mp4"
    ff.run(["-loop", "1", "-i", img, "-i", str(tone), "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(out)])
    return str(out)


def test_speech_bounds_and_tail_trim(speech_clip, tmp_path):
    start, end = ff.speech_bounds(speech_clip)
    assert start < 0.2 and 1.3 < end < 1.8
    out, removed = ff.trim_tail(speech_clip, str(tmp_path / "t.mp4"), tail=0.5)
    assert removed > 0.5 and ff.probe(out).duration < 2.5


def test_fit_audio_limits_tempo(tmp_path):
    a = ff.make_tone(str(tmp_path / "a.wav"), 4.0)
    out, factor = ff.fit_audio(a, 2.0, str(tmp_path / "f.wav"))  # would need 2x: capped at 1.25
    assert factor == 1.25 and abs(ff.probe(out).duration - 2.0) < 0.05
    out2, f2 = ff.fit_audio(a, 6.0, str(tmp_path / "g.wav"))  # shorter speech: padded, not slowed
    assert f2 == 1.0 and abs(ff.probe(out2).duration - 6.0) < 0.05
    assert ff.atempo_chain(3.0).count("atempo") == 2


def test_editor_assembles_vertical_h264_aac(speech_clip, tmp_path, product_image):
    no_audio = str(tmp_path / "silent.mp4")
    ff.run(["-loop", "1", "-i", ff.make_still(str(tmp_path / "x.png"), 360, 640), "-t", "2", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", no_audio])
    clips = [SceneClip(speech_clip, "Look at this bottle", 3, trim_speech_tail=True),
             SceneClip(no_audio, "", 2, trim_speech_tail=False, overlay_product=True)]
    res = VideoEditor().assemble(clips, EditSettings(cta="Shop now", brand="Aqua", product_image=product_image),
                                 workdir=str(tmp_path / "wd"))
    info = ff.probe(res.video_path)
    assert (info.width, info.height, info.vcodec, info.acodec) == (1080, 1920, "h264", "aac")
    assert 4.0 < info.duration < 7.5
    assert res.srt_path and "Look at this bottle" in open(res.srt_path).read()
    assert os.path.exists(res.thumbnail_path)
    assert res.timeline[-1]["scene"] == "end_card"
    qa = QualityAssurance(HeuristicLLM(), NoTranscription()).check_export(res.video_path, target_duration=5)
    assert qa.passed, qa.issues
    assert {c["check"] for c in qa.checks} >= {"resolution", "video_codec", "audio_codec", "export_integrity", "loudness"}


def test_export_qa_fails_wrong_resolution(speech_clip):
    r = QualityAssurance(HeuristicLLM(), NoTranscription()).check_export(speech_clip, target_duration=3)
    assert not r.passed and any(i["check"] == "resolution" for i in r.issues)


def test_scene_qa_without_vision_marks_not_checked(speech_clip):
    r = QualityAssurance(HeuristicLLM(), NoTranscription()).check_scene(
        clip=speech_clip, dialogue="hello", language="en", audio_source="native", lipsync_status="native",
        anchor_image=None, product_image=None, expects_product=False)
    statuses = {c["check"]: c["status"] for c in r.checks}
    assert statuses["identity"] == "not_checked" and statuses["dialogue_accuracy"] == "not_checked"
    assert r.passed  # nothing failed - but nothing was claimed as visually verified either


class FakeVision:
    name = "fake"
    supports_vision = True

    def __init__(self, identity_score):
        self.identity_score = identity_score
        self.calls = 0

    def structured(self, *, system, prompt, schema, images=None, task="", fallback=None):
        self.calls += 1
        assert any(i.label == "IDENTITY REFERENCE" for i in images)
        return SceneVisualQA(identity_match=self.identity_score >= 0.8, identity_score=self.identity_score,
                             product_accuracy="not_applicable", invented_branding=False, hand_anatomy_ok=True,
                             visual_artifacts=False, continuity_ok=True,
                             issues=[] if self.identity_score >= 0.8 else [QAIssue(check="identity", severity="high", detail="different face")],
                             overall_score=self.identity_score), LLMUsage(model="fake")


def test_scene_qa_identity_failure_is_regenerable(speech_clip, product_image):
    r = QualityAssurance(FakeVision(0.4), NoTranscription()).check_scene(
        clip=speech_clip, dialogue="hello", language="en", audio_source="native", lipsync_status="native",
        anchor_image=product_image, product_image=None, expects_product=False)
    assert not r.passed and r.regenerable
    ok = QualityAssurance(FakeVision(0.92), NoTranscription()).check_scene(
        clip=speech_clip, dialogue="hello", language="en", audio_source="native", lipsync_status="native",
        anchor_image=product_image, product_image=None, expects_product=False)
    assert ok.passed


class FakeTranscriber:
    name = "fake"

    def __init__(self, text):
        self.text = text

    def available(self):
        return True

    def transcribe(self, path, language=None):
        return self.text


def test_dialogue_accuracy_check(speech_clip):
    good = QualityAssurance(HeuristicLLM(), FakeTranscriber("Look at this bottle!")).check_scene(
        clip=speech_clip, dialogue="Look at this bottle.", language="en", audio_source="native",
        lipsync_status="native", anchor_image=None, product_image=None, expects_product=False)
    bad = QualityAssurance(HeuristicLLM(), FakeTranscriber("Hey guys welcome to my channel")).check_scene(
        clip=speech_clip, dialogue="Look at this bottle.", language="en", audio_source="native",
        lipsync_status="native", anchor_image=None, product_image=None, expects_product=False)
    assert good.passed and not bad.passed and bad.regenerable
    assert dialogue_similarity("Schau dir das an", "schau dir das an!") == 1.0
