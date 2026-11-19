# Phase 1: Reference analysis and LetzAI compatibility matrix

This file covers two sources:

* **Reference repository:** [`kofiowusuai-lab/ugc-skills`](https://github.com/kofiowusuai-lab/ugc-skills).
  * MIT licence, © 2026 Kofi Owusu.
  * It is a set of Claude Code *skills* (Markdown) plus bash/Python wrappers.
  * The wrappers drive the Grok CLI, `claude -p`, Gemini, ElevenLabs, WaveSpeed and FFmpeg.
  * It is not a service.
* **LetzAI documentation, inspected 2026-11-19:**
  * The public OpenAPI spec (`https://api.letz.ai/doc-yaml`).
  * `https://letz.ai/systemprompts/api_instructions.md`.
  * The live model catalogue (`https://letz.ai/docs/models.json`, also served at `GET /catalog`).

## What LetzAI's public API actually offers

| Capability | Endpoint | Notes used by this project |
|---|---|---|
| Text-to-image | `POST /images` | `width`/`height` are 480–2160. No image input. No `aspectRatio`, `seed` or `negativePrompt`; unknown fields return 400. |
| Image-to-image / multi-reference | `POST /image-edits`, `mode=context` | `inputImageUrls` takes up to 9 images. `settings.aspect_ratio` supports `9:16`. The result is at `generatedImageCompletion.imageVersions.original`. |
| Text-to-video | `POST /videos` with no image | Only on models with `supportsTextToVideo`. |
| Image-to-video | `POST /videos` with `imageUrl` (+ `secondFrameUrl`) | Per-model `settings.mode`, `duration` and `resolution`. |
| Reference assets | `POST /videos` with `assetUrls` | The number of references per model comes from the catalogue (`allowed_references`). |
| Multi-shot | Kling 4 timed shot list in `prompt` | Supported by the API. The pipeline uses one shot per request for finer QA and regeneration. |
| Native synchronized audio | `alwaysAudio` / `allowAudio` models | Seedance 2.5, Kling 4, Gemini Omni and Flux 3 generate speech *inside* the clip. |
| Speech (TTS) | `POST /audios`, `kind=speech` | Models `audio-eleven-v4` (default), `audio-gemini-tts`, `audio-openai-tts`. Six voice presets. `language` is supported (`en`, `de`, …). |
| Music / SFX | `POST /audios`, `kind=music` / `sound_effect` | Used for the optional music bed. |
| Uploads | `POST /user-assets`, then PUT to the presigned `uploadUrl` | The PUT carries **no** Authorization header. |
| Status | `GET /images|/image-edits|/videos|/audios/{id}` | Terminal success: `ready` (and `saved` for videos and edits). Failure: `failed`, `interrupted`, `not_allowed`. |
| Webhooks | `webhookUrl` on create requests | **No payload schema or signature is documented.** We authenticate with a per-job HMAC token in the URL and always re-fetch the job state. |
| Cost estimate | `POST /generations/quote` | Never charges. The catalogue holds per-model list prices. |
| Model discovery | `GET /catalog` (and `GET /models` for trained `@handles`) | Limits are machine-readable: duration min/max, resolutions, aspect ratios and audio. |
| Cancellation | `PUT /images/{id}/interruption` | **There is no video interruption endpoint.** |
| Lip-sync | — | **No public lip-sync endpoint.** Catalogue matches for "lip" are only the word "c*lip*". |
| Transcription / vision QA | — | Not offered, so external providers are required. |

## Feature migration matrix

| Reference feature (file) | Status | Implementation here |
|---|---|---|
| **ugc-ad-strategist**: brief schema, angles, hook menu, beat sheet, "one claim", no income/result claims (`skills/ugc-ad-strategist/*`) | **Migrated with modification** | `agents/strategist.py`, `agents/prompts.py`. Concepts include hook, core message, emotional angle, visual concept, CTA and duration. Claims must cite researched evidence. The reference's *first-person past-tense testimonial* rule was **dropped on purpose**: our creators are fictional, so fabricated experience is rejected by `fabricated_experience_flags()`. |
| Ad-library scraping (`ad_library_scout.py`) | **Not migrated** | It scrapes Meta and TikTok without permission. That conflicts with the "respect robots/terms" requirement. |
| Product grounding (strategist "Ground" stage) | **Migrated with modification** | `agents/researcher.py` + `research/`. A search swarm modelled on the SID-2 report crawls the product page and same-site pages (SSRF-safe, robots.txt). Claims must quote retrieved passages and are verified to the character span ([RESEARCH.md](RESEARCH.md)). |
| **Shot planner** + script writer (`ugc_shot_planner.sh`, `ugc_write_script.sh`) | **Migrated with modification** | `agents/scene_director.py`. Scene length is fitted to the **catalogue limits of the selected LetzAI model**, not the fixed 6/10 s of Grok. Word budget is 2.5 words/s (EN) and 2.2 (DE). |
| **Character anchor / bible** (`ugc_character_bible.sh`) | **Migrated with modification** | `agents/creator_director.py` + creator library. The anchor is made with `POST /images`. Per-scene keyframes come from `POST /image-edits` with anchor plus real product photo, using the identity-lock prompt from the reference. Real people need recorded consent. |
| **Realism prompt rules** (`realism_prompts.md`) | **Migrated directly** (rewritten) | `agents/prompts.py`: realism stack, identity lock, banned "quality" words. This also matches LetzAI's own prompt guidance. |
| Grok image-to-video candidates (`ugc_grok_candidates.sh`, `grok_imagine.py`) | **Replaced by LetzAI** | `providers/letzai/*` and `agents/video_producer.py`. Async submit, poll and webhook with N candidates per scene. Provider job IDs are persisted. |
| Dialogue hard-lock ("say these EXACT words…", QA bank D0) | **Migrated directly** | `prompts.dialogue_lock()`. |
| Vision referee: identity ≥ 0.80, frames at 15/50/85 % (`ugc_clip_referee.py`, `ugc_gemini_referee.py`) | **Migrated with modification** | `agents/qa.py` uses a provider-agnostic `LLMProvider` (Claude via structured outputs). Checks that cannot run are reported as `not_checked`, never as passed. |
| Whisper transcript check, similarity ≥ 0.86 (QA bank D0) | **Requires an additional provider** | `providers/transcription.py`: optional `faster-whisper`. |
| ElevenLabs TTS / STS (`voice_and_lipsync.py`, `ugc_add_voice.py`) | **Replaced by LetzAI** | `POST /audios` speech. The model `audio-eleven-v4` is ElevenLabs served by LetzAI. Voice identity is the creator's stored preset. **STS (voice swap) is not available** on LetzAI's public API. |
| TTS stretch with rubberband (`vendor/voiceswap/stretch.py`) | **Modified** | Uses FFmpeg `atempo`, clamped to 0.8–1.25×. This avoids the GPL rubberband CLI. Outside that range we pad or trim rather than distort the speech. |
| WaveSpeed lip-sync (`vendor/voiceswap/wavespeed.py`) | **Requires an additional provider** | `providers/lipsync.py`, `WaveSpeedLipSync`, is a port of the reference flow. It is **not verified** against a live account. The default is native model audio, so lip-sync is only needed in TTS mode. |
| Tail trim by RMS (`trim_clip_tails.py`) | **Migrated directly** | `media/ffmpeg.speech_bounds/trim_tail` (frac 0.045, tail 0.85 s, min cut 0.35 s, never pads). |
| Stitching + loudness (`stitch_shots.sh`, QA bank F4) | **Migrated with modification** | Output is 1080×1920, 30 fps, H.264 CRF 18, AAC 48 kHz, hard cuts, `loudnorm I=-16:TP=-1.5:LRA=11`, and the `0:V:0` mapping trick. |
| Captions (`ugc_captions.py` + unbundled Remotion) | **Modified** | SRT cues of ≤ 6 words are timed by detected speech bounds and burned in with libass. A sidecar `.srt` is exported. |
| Device-screen compositing (`pdf_screen.py`, PyMuPDF/AGPL) | **Not migrated** | Uses an AGPL dependency and screen-tracking heuristics. We keep the principle: **real product imagery is composited** (product overlay and end card) instead of AI-rendered branding. |
| Book mockup / Ken Burns (`book_mockup.py`) | **Partially** | The end card uses the real product photo plus FFmpeg-rendered text. |
| B-roll / SFX / Remotion studio matte | **Not migrated** | Depends on unbundled Remotion. Optional LetzAI music covers the "optional music" requirement. |
| ugc-minimax-mode (blind-agent variant) | **Superseded** | The whole pipeline is code-driven. Its hard rules ("never ship unrefereed clip", min 0.80) are enforced in `stages.stage_qa`. |
| Telegram task monitor | **Replaced** | Web production monitor, structured logs, and `provider_requests` audit table. |

## Licences

* **Reference repo:** MIT. Ported algorithms keep attribution in their module docstrings and in [`THIRD_PARTY.md`](THIRD_PARTY.md).
* **FFmpeg:** invoked as an external process. The Debian build includes GPL components such as libx264, so that licence applies to the distributed image.
* **Not used:** rubberband (GPL) and PyMuPDF (AGPL) are deliberately absent.
