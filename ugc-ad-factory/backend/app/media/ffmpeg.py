"""FFmpeg / FFprobe helpers for assembly and technical QA.

Several parameters are ported (MIT) from kofiowusuai-lab/ugc-skills:
  * per-clip normalisation (scale→crop→fps, libx264 crf 18, yuv420p, AAC)
  * mapping `0:V:0` (capital V) so generator cover-art streams are ignored
  * RMS-based speech-end detection for tail trimming (silencedetect fails on
    generated room tone) with tail=0.85s, min_cut=0.35s, frac=0.045
  * final loudness pass loudnorm=I=-16:TP=-1.5:LRA=11
Stretching uses ffmpeg `atempo` (LGPL build-compatible) instead of the GPL
rubberband CLI used by the reference repo.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass, field

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"

FONT_CANDIDATES = [
    os.environ.get("UGC_FONT_FILE", ""),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

OUT_W, OUT_H, OUT_FPS = 1080, 1920, 30
AUDIO_RATE = 48000


class FFmpegError(RuntimeError):
    pass


def run(args: list[str], timeout: int = 900) -> subprocess.CompletedProcess:
    cmd = [FFMPEG, "-hide_banner", "-nostdin", "-y", "-loglevel", "error", *args]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise FFmpegError(f"ffmpeg failed ({p.returncode}): {p.stderr.strip()[-1500:]}")
    return p


def run_analysis(args: list[str], timeout: int = 600) -> str:
    """Run an ffmpeg analysis filter and return stderr (where filters log)."""
    cmd = [FFMPEG, "-hide_banner", "-nostdin", "-loglevel", "info", *args]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise FFmpegError(p.stderr.strip()[-1500:])
    return p.stderr


def font_file() -> str | None:
    for f in FONT_CANDIDATES:
        if f and os.path.exists(f):
            return f
    return None


# ------------------------------------------------------------------ probing
@dataclass
class MediaInfo:
    duration: float = 0.0
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    vcodec: str | None = None
    acodec: str | None = None
    has_video: bool = False
    has_audio: bool = False
    pix_fmt: str | None = None
    sample_rate: int | None = None
    format_name: str | None = None
    raw: dict = field(default_factory=dict)


def probe(path: str) -> MediaInfo:
    p = subprocess.run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format",
                        "-show_streams", path], capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise FFmpegError(f"ffprobe failed: {p.stderr.strip()[-500:]}")
    data = json.loads(p.stdout or "{}")
    info = MediaInfo(raw=data)
    fmt = data.get("format", {})
    info.format_name = fmt.get("format_name")
    info.duration = float(fmt.get("duration") or 0)
    for st in data.get("streams", []):
        if st.get("codec_type") == "video" and not st.get("disposition", {}).get("attached_pic"):
            if info.has_video:
                continue
            info.has_video = True
            info.vcodec = st.get("codec_name")
            info.width, info.height = st.get("width"), st.get("height")
            info.pix_fmt = st.get("pix_fmt")
            num, _, den = (st.get("avg_frame_rate") or "0/1").partition("/")
            try:
                info.fps = float(num) / float(den or 1) if float(den or 1) else None
            except ValueError:
                info.fps = None
            if not info.duration:
                info.duration = float(st.get("duration") or 0)
        elif st.get("codec_type") == "audio" and not info.has_audio:
            info.has_audio = True
            info.acodec = st.get("codec_name")
            info.sample_rate = int(st.get("sample_rate") or 0) or None
    return info


# ------------------------------------------------------------------ synthesis (mock + cards)
def make_still(out: str, w: int, h: int, color: str = "0x6b8f71", accent: str = "0xf2e3c6") -> str:
    """Simple synthetic 'portrait' plate: background + head/body shapes."""
    vf = (f"drawbox=x={w//2 - w//6}:y={h//4}:w={w//3}:h={h//5}:color={accent}@1:t=fill,"
          f"drawbox=x={w//2 - w//4}:y={h//4 + h//5}:w={w//2}:h={h//3}:color={accent}@0.8:t=fill")
    run(["-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}", "-vf", vf, "-frames:v", "1", out])
    return out


def make_clip_from_image(image: str, out: str, duration: float, w: int = 720, h: int = 1280,
                         fps: int = 24, tone_hz: int | None = None) -> str:
    """Slow push-in on a still; optional tone track (used by the mock provider)."""
    frames = max(1, int(duration * fps))
    vf = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
          f"zoompan=z='min(zoom+0.0008,1.12)':d={frames}:s={w}x{h}:fps={fps},format=yuv420p")
    args = ["-loop", "1", "-i", image]
    if tone_hz:
        args += ["-f", "lavfi", "-i", f"sine=frequency={tone_hz}:sample_rate={AUDIO_RATE}"]
    args += ["-vf", vf, "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "veryfast",
             "-pix_fmt", "yuv420p"]
    if tone_hz:
        args += ["-af", "volume=0.25,tremolo=f=4:d=0.7", "-c:a", "aac", "-ar", str(AUDIO_RATE),
                 "-shortest"]
    run(args + [out])
    return out


def make_tone(out: str, duration: float, hz: int = 220) -> str:
    run(["-f", "lavfi", "-i", f"sine=frequency={hz}:sample_rate={AUDIO_RATE}", "-t", f"{duration:.3f}",
         "-af", "volume=0.3,tremolo=f=5:d=0.8", "-ac", "1", out])
    return out


# ------------------------------------------------------------------ extraction
def extract_frame(video: str, t: float, out: str, width: int | None = 540) -> str:
    vf = ["-vf", f"scale={width}:-2"] if width else []
    run(["-ss", f"{max(0.0, t):.3f}", "-i", video, "-map", "0:V:0", "-frames:v", "1", *vf, out])
    return out


def extract_audio(video: str, out: str, rate: int = AUDIO_RATE, mono: bool = False) -> str:
    run(["-i", video, "-map", "0:a:0", "-vn", "-ac", "1" if mono else "2", "-ar", str(rate),
         "-c:a", "pcm_s16le", out])
    return out


# ------------------------------------------------------------------ speech-end detection (ported)
def _read_wav_mono16(path: str) -> tuple[list[int], int]:
    import wave
    with wave.open(path, "rb") as w:
        rate, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if sw != 2:
        raise FFmpegError("expected 16-bit PCM")
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    if ch > 1:
        samples = samples[::ch]
    return list(samples), rate


def speech_bounds(audio_or_video: str, frac: float = 0.045, window: float = 0.05,
                  min_run: int = 2) -> tuple[float, float] | None:
    """(start, end) of speech using windowed RMS against peak*frac."""
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        try:
            run(["-i", audio_or_video, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                 "-c:a", "pcm_s16le", wav])
        except FFmpegError:
            return None
        samples, rate = _read_wav_mono16(wav)
    win = max(1, int(rate * window))
    rms = []
    for i in range(0, len(samples), win):
        chunk = samples[i:i + win]
        if not chunk:
            break
        rms.append(math.sqrt(sum(x * x for x in chunk) / len(chunk)))
    if not rms:
        return None
    thr = max(rms) * frac
    if max(rms) <= 0:
        return None
    above = [r > thr for r in rms]
    start = end = None
    for i in range(len(above) - min_run + 1):
        if all(above[i:i + min_run]):
            start = i
            break
    for i in range(len(above) - 1, min_run - 2, -1):
        if all(above[i - min_run + 1:i + 1]):
            end = i + 1
            break
    if start is None or end is None:
        return None
    return start * window, end * window


def trim_tail(video: str, out: str, tail: float = 0.85, min_cut: float = 0.35) -> tuple[str, float]:
    """Cut trailing silence (generated mouth motion after speech reads fake).
    Never pads past the source. Returns (path, seconds_removed)."""
    info = probe(video)
    bounds = speech_bounds(video) if info.has_audio else None
    if not bounds:
        shutil.copyfile(video, out)
        return out, 0.0
    target = min(info.duration, bounds[1] + tail)
    cut = info.duration - target
    if cut < min_cut:
        shutil.copyfile(video, out)
        return out, 0.0
    run(["-i", video, "-t", f"{target:.3f}", "-map", "0:V:0", "-map", "0:a:0", "-c:v", "libx264",
         "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", str(AUDIO_RATE), "-ac", "2", out])
    return out, cut


# ------------------------------------------------------------------ normalisation & audio
def normalize_clip(src: str, out: str, w: int = OUT_W, h: int = OUT_H, fps: int = OUT_FPS,
                   duration: float | None = None) -> str:
    """Scale/crop to the delivery frame, constant fps, stereo AAC; injects a
    silent track when the clip has no audio so concat stays aligned."""
    info = probe(src)
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1,format=yuv420p"
    args = ["-i", src]
    if not info.has_audio:
        args += ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_RATE}"]
    args += ["-map", "0:V:0", "-map", "0:a:0" if info.has_audio else "1:a:0", "-vf", vf]
    if duration:
        args += ["-t", f"{duration:.3f}"]
    elif not info.has_audio:
        args += ["-shortest"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE), "-ac", "2", "-movflags", "+faststart",
             out]
    run(args)
    return out


def atempo_chain(factor: float) -> str:
    """atempo accepts 0.5..2.0 per instance; chain for other values."""
    parts = []
    while factor > 2.0:
        parts.append("atempo=2.0")
        factor /= 2.0
    while factor < 0.5:
        parts.append("atempo=0.5")
        factor /= 0.5
    parts.append(f"atempo={factor:.5f}")
    return ",".join(parts)


def fit_audio(audio: str, target: float, out: str, min_factor: float = 0.8,
              max_factor: float = 1.25) -> tuple[str, float]:
    """Fit speech to a slot. Tempo change only within [0.8, 1.25] (outside that
    range speech sounds unnatural); otherwise pad with silence / trim."""
    dur = probe(audio).duration
    factor = dur / target if target > 0 else 1.0
    filters = []
    applied = 1.0
    if abs(factor - 1.0) > 0.02:
        applied = min(max_factor, max(min_factor, factor)) if factor > 1.0 else 1.0
        if applied != 1.0:
            filters.append(atempo_chain(applied))
    filters.append(f"apad=whole_dur={target:.3f}")
    run(["-i", audio, "-af", ",".join(filters), "-t", f"{target:.3f}", "-ar", str(AUDIO_RATE),
         "-ac", "2", "-c:a", "pcm_s16le", out])
    return out, applied


def mux_audio(video: str, audio: str, out: str) -> str:
    """Replace the clip's audio track; output length = video length."""
    dur = probe(video).duration
    run(["-i", video, "-i", audio, "-map", "0:V:0", "-map", "1:a:0", "-c:v", "copy",
         "-af", f"apad=whole_dur={dur:.3f}", "-t", f"{dur:.3f}", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(AUDIO_RATE), "-ac", "2", out])
    return out


def mix_music(video: str, music: str, out: str, music_db: float = -20.0) -> str:
    run(["-i", video, "-stream_loop", "-1", "-i", music, "-filter_complex",
         f"[1:a]volume={music_db}dB[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
         "-map", "0:V:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])
    return out


def concat(clips: list[str], out: str) -> str:
    """Concat normalised clips with hard cuts (re-encode for safety)."""
    if not clips:
        raise FFmpegError("nothing to concat")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
        lst = f.name
    try:
        run(["-f", "concat", "-safe", "0", "-i", lst, "-map", "0:V:0", "-map", "0:a:0",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-r", str(OUT_FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE), "-ac", "2",
             "-movflags", "+faststart", out])
    finally:
        os.unlink(lst)
    return out


def loudnorm(src: str, out: str, i: float = -16.0, tp: float = -1.5, lra: float = 11.0) -> str:
    run(["-i", src, "-map", "0:V:0", "-map", "0:a:0", "-c:v", "copy",
         "-af", f"loudnorm=I={i}:TP={tp}:LRA={lra}", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(AUDIO_RATE), "-movflags", "+faststart", out])
    return out


# ------------------------------------------------------------------ overlays, subtitles, cards
def _esc_drawtext(s: str) -> str:
    return s.replace("\\", "\\\\").replace(":", r"\:").replace("'", "\u2019").replace("%", r"\%")


def wrap_words(text: str, max_chars: int = 22) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def caption_cues(text: str, start: float, end: float, max_words: int = 6) -> list[tuple[float, float, str]]:
    """Split a line into short cues (≤ ~6 words) timed proportionally to word count."""
    words = text.split()
    if not words or end <= start:
        return []
    chunks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
    per = (end - start) / len(words)
    cues, t = [], start
    for ch in chunks:
        d = per * len(ch)
        cues.append((t, t + d, " ".join(ch)))
        t += d
    return cues


def _srt_ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: list[tuple[float, float, str]], path: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, t) in enumerate(cues, 1):
            f.write(f"{i}\n{_srt_ts(a)} --> {_srt_ts(b)}\n{t}\n\n")
    return path


def burn_subtitles(src: str, srt: str, out: str) -> str:
    style = ("FontName=DejaVu Sans,Bold=1,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=70")
    srt_esc = srt.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    run(["-i", src, "-map", "0:V:0", "-map", "0:a:0", "-vf",
         f"subtitles='{srt_esc}':force_style='{style}'", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", out])
    return out


def overlay_image(src: str, image: str, out: str, start: float, end: float,
                  width_frac: float = 0.42, y_frac: float = 0.08) -> str:
    """Overlay a real product image (exact branding preserved) in a time window."""
    info = probe(src)
    w = int((info.width or OUT_W) * width_frac) // 2 * 2
    y = int((info.height or OUT_H) * y_frac)
    fc = (f"[1:v]scale={w}:-2,format=rgba[ov];"
          f"[0:v][ov]overlay=x=(W-w)/2:y={y}:enable='between(t,{start:.2f},{end:.2f})'[v]")
    run(["-i", src, "-i", image, "-filter_complex", fc, "-map", "[v]", "-map", "0:a:0",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", out])
    return out


def end_card(out: str, duration: float, lines: list[str], image: str | None = None,
             w: int = OUT_W, h: int = OUT_H, bg: str = "0x111111") -> str:
    """End card built from the real product image + text rendered by FFmpeg
    (never AI-generated text)."""
    font = font_file()
    inputs = ["-f", "lavfi", "-i", f"color=c={bg}:s={w}x{h}:r={OUT_FPS}:d={duration:.3f}"]
    chain = "[0:v]"
    filters = []
    if image:
        inputs += ["-loop", "1", "-t", f"{duration:.3f}", "-i", image]
        filters.append(f"[1:v]scale={int(w * 0.7)}:{int(h * 0.42)}:force_original_aspect_ratio=decrease[p]")
        filters.append(f"{chain}[p]overlay=x=(W-w)/2:y={int(h * 0.16)}[b]")
        chain = "[b]"
    if font:
        y = int(h * 0.64)
        for i, line in enumerate(lines[:4]):
            size = 72 if i == 0 else 52
            filters.append(f"{chain}drawtext=fontfile='{font}':text='{_esc_drawtext(line)}':"
                           f"fontcolor=white:fontsize={size}:x=(w-text_w)/2:y={y}[t{i}]")
            chain = f"[t{i}]"
            y += size + 34
    filters.append(f"{chain}format=yuv420p[v]")
    inputs += ["-f", "lavfi", "-t", f"{duration:.3f}", "-i",
               f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_RATE}"]
    audio_idx = 2 if image else 1
    run([*inputs, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", f"{audio_idx}:a:0",
         "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(OUT_FPS), "-c:a", "aac", "-ar", str(AUDIO_RATE), "-ac", "2", out])
    return out


def thumbnail(video: str, out: str) -> str:
    info = probe(video)
    return extract_frame(video, min(1.0, info.duration / 3), out, width=540)


# ------------------------------------------------------------------ technical QA measurements
@dataclass
class AudioStats:
    max_volume_db: float | None
    mean_volume_db: float | None
    integrated_lufs: float | None
    true_peak_db: float | None


def audio_stats(path: str) -> AudioStats:
    try:
        err = run_analysis(["-i", path, "-map", "0:a:0", "-af", "volumedetect,ebur128=peak=true",
                            "-f", "null", "-"])
    except FFmpegError:
        return AudioStats(None, None, None, None)

    def grab(pat):
        m = re.findall(pat, err)
        return float(m[-1]) if m else None

    return AudioStats(max_volume_db=grab(r"max_volume:\s*(-?[\d.]+|-inf) dB") if "max_volume" in err else None,
                      mean_volume_db=grab(r"mean_volume:\s*(-?[\d.]+) dB"),
                      integrated_lufs=grab(r"I:\s*(-?[\d.]+) LUFS"),
                      true_peak_db=grab(r"Peak:\s*(-?[\d.]+) dBFS"))


def black_segments(path: str, min_dur: float = 0.5) -> list[tuple[float, float]]:
    err = run_analysis(["-i", path, "-map", "0:V:0", "-vf", f"blackdetect=d={min_dur}:pix_th=0.10",
                        "-an", "-f", "null", "-"])
    return [(float(a), float(b)) for a, b in
            re.findall(r"black_start:(\d+\.?\d*)\s+black_end:(\d+\.?\d*)", err)]


def frozen_segments(path: str, min_dur: float = 1.5) -> list[tuple[float, float]]:
    err = run_analysis(["-i", path, "-map", "0:V:0", "-vf", f"freezedetect=n=-60dB:d={min_dur}",
                        "-an", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"freeze_start: (\d+\.?\d*)", err)]
    ends = [float(x) for x in re.findall(r"freeze_end: (\d+\.?\d*)", err)]
    return list(zip(starts, ends + [probe(path).duration] * (len(starts) - len(ends))))


def decode_ok(path: str) -> tuple[bool, str]:
    p = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "null", "-"], capture_output=True,
                       text=True, timeout=600)
    return (p.returncode == 0 and not p.stderr.strip(), p.stderr.strip()[:500])
