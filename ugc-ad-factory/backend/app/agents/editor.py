"""Agent 8 - Video Editor: FFmpeg assembly to 1080x1920 H.264/AAC MP4.

Order: per-scene tail trim (native speech) -> normalise -> optional real
product overlay -> concat (hard cuts) -> end card from real product image +
FFmpeg-rendered text -> optional music bed -> burned captions -> loudnorm.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

from app.media import ffmpeg as ff


@dataclass
class SceneClip:
    path: str
    dialogue: str
    planned_duration: float
    trim_speech_tail: bool
    overlay_product: bool = False


@dataclass
class EditSettings:
    subtitles: bool = True
    end_card: bool = True
    end_card_seconds: float = 2.0
    cta: str | None = None
    brand: str | None = None
    product_image: str | None = None
    music_path: str | None = None
    music_db: float = -22.0
    width: int = ff.OUT_W
    height: int = ff.OUT_H


@dataclass
class EditResult:
    video_path: str
    srt_path: str | None
    thumbnail_path: str
    duration: float
    timeline: list[dict] = field(default_factory=list)


class VideoEditor:
    def assemble(self, clips: list[SceneClip], settings: EditSettings, workdir: str | None = None) -> EditResult:
        wd = workdir or tempfile.mkdtemp(prefix="edit_")
        os.makedirs(wd, exist_ok=True)
        normalized, cues, timeline = [], [], []
        t = 0.0
        for i, c in enumerate(clips):
            src = c.path
            if c.trim_speech_tail:
                trimmed = os.path.join(wd, f"trim_{i}.mp4")
                src, removed = ff.trim_tail(src, trimmed)
            else:
                removed = 0.0
            norm = os.path.join(wd, f"norm_{i}.mp4")
            info = ff.probe(src)
            cap = None if c.trim_speech_tail else min(info.duration, c.planned_duration + 0.25)
            ff.normalize_clip(src, norm, settings.width, settings.height, duration=cap)
            if c.overlay_product and settings.product_image:
                ov = os.path.join(wd, f"ov_{i}.mp4")
                d = ff.probe(norm).duration
                ff.overlay_image(norm, settings.product_image, ov, start=max(0, d - 2.2), end=d)
                norm = ov
            d = ff.probe(norm).duration
            speech = ff.speech_bounds(norm) if c.dialogue else None
            s0, s1 = (speech if speech else (0.0, d))
            cues += ff.caption_cues(c.dialogue, t + s0, t + min(d, s1)) if c.dialogue else []
            timeline.append({"scene": i, "start": round(t, 3), "duration": round(d, 3), "tail_trimmed": round(removed, 3)})
            normalized.append(norm)
            t += d
        if settings.end_card:
            card = os.path.join(wd, "endcard.mp4")
            lines = [l for l in [settings.brand, settings.cta] if l]
            ff.end_card(card, settings.end_card_seconds, [w for l in lines for w in ff.wrap_words(l, 22)],
                        image=settings.product_image, w=settings.width, h=settings.height)
            normalized.append(card)
            timeline.append({"scene": "end_card", "start": round(t, 3), "duration": settings.end_card_seconds})
        joined = ff.concat(normalized, os.path.join(wd, "joined.mp4"))
        cur = joined
        if settings.music_path:
            cur = ff.mix_music(cur, settings.music_path, os.path.join(wd, "music.mp4"), settings.music_db)
        srt = None
        if cues:
            srt = ff.write_srt(cues, os.path.join(wd, "captions.srt"))
            if settings.subtitles:
                cur = ff.burn_subtitles(cur, srt, os.path.join(wd, "subs.mp4"))
        final = ff.loudnorm(cur, os.path.join(wd, "final.mp4"))
        thumb = ff.thumbnail(final, os.path.join(wd, "thumb.jpg"))
        return EditResult(final, srt, thumb, ff.probe(final).duration, timeline)
