"""Pipeline stages. Each stage is idempotent: it inspects persisted state,
creates whatever work is missing, and returns

  DONE   - stage complete, move to the next one
  WAIT   - provider jobs are in flight; a job completion re-triggers advance
  PAUSE  - awaiting human approval / budget confirmation
  GOTO:x - jump back (QA regeneration)

so an interrupted workflow resumes exactly where it stopped.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import audio_director, lipsync_specialist, video_producer
from app.agents.creator_director import CreatorDirector, anchor_prompt
from app.agents.editor import EditSettings, SceneClip, VideoEditor
from app.agents.qa import QualityAssurance
from app.agents.researcher import ProductResearcher
from app.agents.scene_director import SceneDirector, compose_prompts
from app.agents.schemas import Beat, ProductResearch
from app.agents.strategist import AdvertisingStrategist
from app.core.config import get_settings
from app.db.models import (AdConcept, Creator, CreatorReference, Export, GeneratedAsset, GenerationJob,
                           Product, ProductAsset, Project, QAReport, Scene, Script, Storyboard, utcnow)
from app.media import ffmpeg as ff
from app.pipeline import costs, dispatch, jobs
from app.providers import registry
from app.services.storage import tmp_dir

STAGES = ["research", "script", "character", "scenes", "video", "voice", "lipsync", "editing", "qa", "export"]
DONE, WAIT, PAUSE = "done", "wait", "pause"


class StageFailed(RuntimeError):
    pass


@dataclass
class Ctx:
    db: Session
    project: Project

    @property
    def st(self) -> dict:
        return self.project.settings or {}

    @property
    def language(self) -> str:
        return self.st.get("language", "en")

    def checkpoint(self, name: str) -> bool:
        """True if the pipeline must pause for approval `name`."""
        return name in (self.st.get("approval_checkpoints") or []) and not (self.project.approvals or {}).get(name)


# ---------------------------------------------------------------- helpers
def _selected_concepts(ctx: Ctx) -> list[AdConcept]:
    return list(ctx.db.scalars(select(AdConcept).where(AdConcept.project_id == ctx.project.id,
                                                       AdConcept.selected.is_(True)).order_by(AdConcept.rank)))


def _storyboard(ctx: Ctx, concept: AdConcept) -> Storyboard | None:
    return ctx.db.scalar(select(Storyboard).where(Storyboard.concept_id == concept.id)
                         .order_by(Storyboard.version.desc()))


def _scenes(ctx: Ctx, active_only: bool = True) -> list[tuple[Scene, Storyboard, AdConcept]]:
    rows = ctx.db.execute(select(Scene, Storyboard, AdConcept)
                          .join(Storyboard, Scene.storyboard_id == Storyboard.id)
                          .join(AdConcept, Storyboard.concept_id == AdConcept.id)
                          .where(Scene.project_id == ctx.project.id, AdConcept.selected.is_(True))
                          .order_by(AdConcept.rank, Scene.idx)).all()
    return [(s, sb, c) for s, sb, c in rows if not active_only or s.status != "failed"]


def _product_image(ctx: Ctx) -> ProductAsset | None:
    prod = ctx.project.product
    if not prod:
        return None
    imgs = [a for a in prod.assets if a.kind in ("image", "screenshot") and a.mime_type.startswith("image/")]
    return imgs[0] if imgs else None


def _product_url(ctx: Ctx) -> str | None:
    pa = _product_image(ctx)
    if not pa:
        return None
    url = jobs.ensure_provider_url(ctx.db, storage_key=pa.storage_key, mime=pa.mime_type,
                                   current=pa.provider_url, project_id=ctx.project.id)
    pa.provider_url = url
    return url


def _asset_url(ctx: Ctx, asset: GeneratedAsset) -> str:
    url = jobs.ensure_provider_url(ctx.db, storage_key=asset.storage_key, mime=asset.mime_type,
                                   current=asset.provider_url, project_id=ctx.project.id)
    asset.provider_url = url
    return url


def _jobs_for(ctx: Ctx, **filters) -> list[GenerationJob]:
    q = select(GenerationJob).where(GenerationJob.project_id == ctx.project.id)
    for k, v in filters.items():
        q = q.where(getattr(GenerationJob, k) == v)
    return list(ctx.db.scalars(q.order_by(GenerationJob.candidate_index)))


def _kick(jobs_: list[GenerationJob]) -> None:
    for j in jobs_:
        if j.status == "pending":
            dispatch.submit_job(j.id)


def _research(ctx: Ctx) -> ProductResearch:
    return ProductResearch.model_validate(ctx.project.product.research)


def _creator(ctx: Ctx) -> Creator:
    return ctx.db.get(Creator, ctx.project.creator_id)


def _video_info(ctx: Ctx, model: str | None = None):
    return registry.media_provider().video_model(model or ctx.st.get("video_model") or get_settings().letzai_video_model)


# ---------------------------------------------------------------- 1 research
def stage_research(ctx: Ctx) -> str:
    prod: Product = ctx.project.product
    if prod.research:
        return DONE
    researcher = ProductResearcher(registry.llm_provider())
    research, page, usage = researcher.run(
        url=prod.url, name=prod.name, brand=prod.brand_name, description=prod.description,
        audience=ctx.st.get("target_audience"), language=ctx.language, image_count=len(prod.assets),
        brand_guidelines=prod.brand_guidelines, agents=int(ctx.st.get("research_agents", 3)),
        effort=ctx.st.get("research_effort", "medium"), metric=ctx.st.get("research_metric", "ndcg"),
        max_pages=int(ctx.st.get("research_max_pages", 6)))
    if page:
        prod.fetch_status = page.status
        prod.page_text = page.text[:20000] if page.text else None
        prod.page_meta = {"title": page.title, "description": page.description, **page.meta,
                          **({"error": page.error} if page.error else {})}
    elif not prod.url:
        prod.fetch_status = "skipped"
    if not research.supported_claims and not prod.description and (not page or page.status != "ok"):
        raise StageFailed("No usable product information: the page could not be fetched "
                          f"({page.status if page else 'no url'}) and no description was provided.")
    prod.research = research.model_dump()
    prod.name = prod.name or research.product_name
    costs.record_llm_usage(ctx.db, ctx.project.id, usage, "research")
    return DONE


# ---------------------------------------------------------------- 2 script
def stage_script(ctx: Ctx) -> str:
    existing = ctx.db.scalars(select(AdConcept).where(AdConcept.project_id == ctx.project.id)).first()
    if not existing:
        research = _research(ctx)
        strategist = AdvertisingStrategist(registry.llm_provider())
        validated, selected, usage = strategist.run(
            research, language=ctx.language, duration=int(ctx.st.get("duration", 20)),
            variants=int(ctx.st.get("variants", 2)), cta=ctx.st.get("cta"),
            audience=ctx.st.get("target_audience"), brand_guidelines=ctx.project.product.brand_guidelines,
            angles=ctx.st.get("angles"))
        costs.record_llm_usage(ctx.db, ctx.project.id, usage, "strategy")
        if not selected:
            raise StageFailed("The strategist produced no compliant concepts: "
                              + "; ".join(p for v in validated for p in v.problems)[:800])
        sel_ids = {id(v) for v in selected}
        order = selected + [v for v in validated if id(v) not in sel_ids]
        for rank, v in enumerate(order):
            d = v.draft
            concept = AdConcept(project_id=ctx.project.id, angle=d.angle, title=d.title, hook=d.hook,
                                core_message=d.core_message, emotional_angle=d.emotional_angle,
                                visual_concept=d.visual_concept, cta=d.cta, target_duration=d.target_duration,
                                claims_used=d.claims_used, score=v.score, rank=rank, selected=id(v) in sel_ids)
            ctx.db.add(concept)
            ctx.db.flush()
            full = " ".join(b.dialogue for b in d.beats)
            ctx.db.add(Script(concept_id=concept.id, version=1, language=ctx.language, full_text=full,
                              beats=[b.model_dump() | {"validation": v.problems} if i == 0 else b.model_dump()
                                     for i, b in enumerate(d.beats)],
                              word_count=len(full.split())))
    if ctx.checkpoint("concepts"):
        ctx.project.stage_detail = "Waiting for concept approval"
        return PAUSE
    return DONE


# ---------------------------------------------------------------- 3 character
def stage_character(ctx: Ctx) -> str:
    s = get_settings()
    creator = _creator(ctx) if ctx.project.creator_id else None
    if creator is None:
        research = _research(ctx)
        spec, usage = CreatorDirector(registry.llm_provider()).design(
            research, ctx.st.get("creator_prefs") or {}, ctx.language)
        costs.record_llm_usage(ctx.db, ctx.project.id, usage, "creator")
        creator = Creator(owner_id=ctx.project.owner_id, name=spec.name,
                          description=f"{spec.age_range}, {spec.appearance}", appearance=spec.model_dump(),
                          voice={"preset": spec.voice_preset, "language": ctx.language,
                                 "model": ctx.st.get("speech_model") or s.letzai_speech_model,
                                 "characteristics": spec.voice_characteristics},
                          status="generating", is_fictional=True, anchor_prompt=anchor_prompt(spec),
                          generation_metadata={"source_project": ctx.project.id})
        ctx.db.add(creator)
        ctx.db.flush()
        ctx.project.creator_id = creator.id
    if creator.anchor_asset_id is None:
        if not creator.is_fictional and not (creator.likeness_consent or {}).get("confirmed"):
            raise StageFailed("Creator depicts a real person but no likeness consent is recorded.")
        n = int(ctx.st.get("anchor_candidates", 1))
        created = []
        for i in range(n):
            req = video_producer.anchor_request(prompt=creator.anchor_prompt or creator.description or creator.name,
                                                model=ctx.st.get("image_model"))
            created.append(jobs.create_job(ctx.db, project_id=ctx.project.id, purpose="anchor", kind="image",
                                           request=req.to_dict(), creator_id=creator.id, candidate_index=i,
                                           model=req.model or s.letzai_image_model,
                                           idempotency_key=jobs.idem_key("anchor", creator.id, i)))
        ctx.db.flush()
        if any(j.status not in jobs.TERMINAL for j in created):
            _kick(created)
            ctx.project.stage_detail = "Generating creator anchor image"
            return WAIT
        ok = [j for j in created if j.status == "succeeded"]
        if not ok:
            creator.status = "failed"
            raise StageFailed("Creator anchor generation failed: " + "; ".join(j.error or "" for j in created))
        # normally the job hook already attached the anchor; this is the fallback path
        best = ok[0]
        best.selected = True
        creator.anchor_asset_id = best.output_asset_id
        creator.status = "ready"
    if ctx.checkpoint("creator"):
        ctx.project.stage_detail = "Waiting for creator approval"
        return PAUSE
    if creator.status == "ready" and (ctx.project.approvals or {}).get("creator"):
        creator.status = "approved"
    return DONE


# ---------------------------------------------------------------- 4 scenes (storyboard + keyframes)
def stage_scenes(ctx: Ctx) -> str:
    s = get_settings()
    creator = _creator(ctx)
    info = _video_info(ctx)
    audio_mode = audio_director.choose_audio_mode(info, ctx.st.get("audio_mode"))
    has_product = _product_image(ctx) is not None
    research = _research(ctx)
    for concept in _selected_concepts(ctx):
        if _storyboard(ctx, concept):
            continue
        script = concept.scripts[-1]
        beats = [Beat.model_validate({k: v for k, v in b.items() if k in Beat.model_fields}) for b in script.beats]
        specs, notes, usage = SceneDirector(registry.llm_provider()).plan(
            beats=beats, concept_title=concept.title, creator=creator.appearance or {},
            product_name=research.product_name, has_product_images=has_product, info=info,
            language=ctx.language, audio_mode=audio_mode)
        costs.record_llm_usage(ctx.db, ctx.project.id, usage, "storyboard")
        sb = Storyboard(concept_id=concept.id, script_id=script.id, video_model=info.key, audio_mode=audio_mode,
                        total_duration=sum(x.duration for x in specs), notes=notes)
        ctx.db.add(sb)
        ctx.db.flush()
        for i, sp in enumerate(specs):
            sp.needs_product_reference = sp.needs_product_reference and has_product
            kf, vp = compose_prompts(sp, creator.appearance or {}, ctx.language, audio_mode)
            ctx.db.add(Scene(storyboard_id=sb.id, project_id=ctx.project.id, idx=i, beat=sp.beat,
                             duration=sp.duration, dialogue=sp.dialogue, framing=sp.framing,
                             creator_movement=sp.creator_movement, product_interaction=sp.product_interaction,
                             environment=sp.environment, required_references=(["creator_anchor"] + (
                                 ["product_image"] if sp.needs_product_reference else [])),
                             keyframe_prompt=kf, video_prompt=vp, audio_requirements=sp.audio_requirements,
                             overlay_text=sp.overlay_text))
        ctx.db.flush()

    # exact estimate before launching expensive video work
    if not ctx.project.budget_confirmed:
        est = costs.estimate_storyboards(ctx.db, ctx.project, registry.media_provider())
        ctx.project.estimated_credits = est["projected_total"]
        if est["projected_total"] > ctx.project.budget_credits:
            ctx.project.stage_detail = (f"Estimated {est['projected_total']} credits exceeds the project budget "
                                        f"of {ctx.project.budget_credits}. Confirm or raise the budget.")
            return "pause_budget"
    if ctx.checkpoint("storyboard"):
        ctx.project.stage_detail = "Waiting for storyboard approval"
        return PAUSE

    # keyframes: anchor + (real product photo) -> scene-specific first frame
    anchor = ctx.db.get(GeneratedAsset, creator.anchor_asset_id)
    anchor_url = _asset_url(ctx, anchor)
    product_url = _product_url(ctx) if has_product else None
    mode = ctx.st.get("keyframes", "per_scene")
    pending = []
    for scene, sb, _ in _scenes(ctx):
        if scene.keyframe_asset_id:
            continue
        needs_product = "product_image" in (scene.required_references or [])
        if mode == "anchor_only" and not needs_product:
            scene.keyframe_asset_id = anchor.id
            continue
        req = video_producer.keyframe_request(prompt=scene.keyframe_prompt, anchor_url=anchor_url,
                                              product_url=product_url if needs_product else None,
                                              model=ctx.st.get("image_model"))
        job = jobs.create_job(ctx.db, project_id=ctx.project.id, purpose="keyframe", kind="image_edit",
                              request=req.to_dict(), scene_id=scene.id, model=req.model or s.letzai_edit_model,
                              idempotency_key=jobs.idem_key("keyframe", scene.id, scene.regen_round))
        if job.status == "succeeded":
            scene.keyframe_asset_id = job.output_asset_id
        elif job.status in ("failed", "cancelled"):
            scene.keyframe_asset_id = anchor.id  # fall back to the identity anchor
        else:
            pending.append(job)
    if pending:
        ctx.db.flush()
        _kick(pending)
        ctx.project.stage_detail = f"Generating {len(pending)} scene keyframe(s)"
        return WAIT
    return DONE


# ---------------------------------------------------------------- 5 video
def stage_video(ctx: Ctx) -> str:
    s = get_settings()
    n_cand = int(ctx.st.get("video_candidates", s.default_video_candidates))
    resolution = ctx.st.get("resolution") or s.letzai_video_resolution
    product_url = _product_url(ctx) if _product_image(ctx) else None
    pending = []
    for scene, sb, concept in _scenes(ctx):
        if scene.video_asset_id:
            continue
        info = _video_info(ctx, sb.video_model)
        kf = ctx.db.get(GeneratedAsset, scene.keyframe_asset_id) if scene.keyframe_asset_id else None
        kf_url = _asset_url(ctx, kf) if kf else None
        refs = [product_url] if (product_url and "product_image" in (scene.required_references or [])) else []
        cands = []
        for c in range(n_cand):
            req = video_producer.video_request(prompt=scene.video_prompt, duration=scene.duration, info=info,
                                               keyframe_url=kf_url, reference_urls=refs, resolution=resolution,
                                               native_audio=sb.audio_mode == "native")
            cands.append(jobs.create_job(ctx.db, project_id=ctx.project.id, purpose="scene_video", kind="video",
                                         request=req.to_dict(), scene_id=scene.id, candidate_index=c,
                                         round=scene.regen_round, model=info.key,
                                         idempotency_key=jobs.idem_key("video", scene.id, scene.regen_round, c)))
        if any(j.status not in jobs.TERMINAL for j in cands):
            pending += cands
            continue
        ok = [j for j in cands if j.status == "succeeded"]
        if ok:
            ok[0].selected = True
            scene.video_asset_id = ok[0].output_asset_id
            scene.final_clip_asset_id = None
            scene.lipsync_status = None
            scene.qa_status = None
        else:
            scene.status = "failed"
    if pending:
        ctx.db.flush()
        _kick(pending)
        ctx.project.stage_detail = f"Rendering {len({j.scene_id for j in pending})} scene video(s)"
        return WAIT
    _fail_concepts_with_failed_scenes(ctx)
    return DONE


def _fail_concepts_with_failed_scenes(ctx: Ctx) -> None:
    for scene, sb, concept in _scenes(ctx, active_only=False):
        if scene.status == "failed" and concept.selected:
            concept.selected = False
            ctx.project.stage_detail = f"Concept '{concept.title}' dropped: scene {scene.idx + 1} failed to render"
    if not _selected_concepts(ctx):
        raise StageFailed("All advertisement variants failed during video generation.")


# ---------------------------------------------------------------- 6 voice
def stage_voice(ctx: Ctx) -> str:
    creator = _creator(ctx)
    voice = (creator.voice or {}).get("preset")
    model = (creator.voice or {}).get("model") or ctx.st.get("speech_model")
    pending = []
    for scene, sb, concept in _scenes(ctx):
        if scene.audio_asset_id or not scene.dialogue:
            if not scene.dialogue:
                scene.audio_source = "none"
            continue
        video = ctx.db.get(GeneratedAsset, scene.video_asset_id)
        if sb.audio_mode == "native" and (video.meta or {}).get("has_audio"):
            scene.audio_source = "native"
            continue
        # TTS (requested, or native model returned no audio track)
        req = audio_director.speech_request(text=scene.dialogue, voice=voice, language=ctx.language, model=model)
        job = jobs.create_job(ctx.db, project_id=ctx.project.id, purpose="speech", kind="speech",
                              request=req.to_dict(), scene_id=scene.id, model=req.model,
                              idempotency_key=jobs.idem_key("speech", scene.id, jobs.idem_key(scene.dialogue)[:40]))
        if job.status == "succeeded":
            scene.audio_asset_id = job.output_asset_id
            scene.audio_source = "tts"
        elif job.status in ("failed", "cancelled"):
            scene.status = "failed"
        else:
            pending.append(job)
    if ctx.st.get("music"):
        for concept in _selected_concepts(ctx):
            sb = _storyboard(ctx, concept)
            req = audio_director.music_request(mood=concept.emotional_angle or "warm, upbeat",
                                               duration=int(sb.total_duration + 3))
            job = jobs.create_job(ctx.db, project_id=ctx.project.id, purpose="music", kind="music",
                                  request=req.to_dict(), model="audio-eleven-music",
                                  idempotency_key=jobs.idem_key("music", concept.id))
            if job.status not in jobs.TERMINAL:
                pending.append(job)
    if pending:
        ctx.db.flush()
        _kick(pending)
        ctx.project.stage_detail = f"Synthesizing {len(pending)} audio track(s)"
        return WAIT
    _fail_concepts_with_failed_scenes(ctx)
    return DONE


# ---------------------------------------------------------------- 7 lip sync
def stage_lipsync(ctx: Ctx) -> str:
    lip = registry.lipsync_provider()
    pending = []
    for scene, sb, concept in _scenes(ctx):
        if scene.final_clip_asset_id:
            continue
        video = ctx.db.get(GeneratedAsset, scene.video_asset_id)
        decision = lipsync_specialist.decide(audio_source=scene.audio_source, has_dialogue=bool(scene.dialogue),
                                             clip_has_audio=bool((video.meta or {}).get("has_audio")),
                                             lipsync_available=lip.available())
        if decision in ("native", "none"):
            scene.lipsync_status = "native" if decision == "native" else "skipped"
            scene.final_clip_asset_id = video.id
            scene.status = "ready"
            continue
        audio = ctx.db.get(GeneratedAsset, scene.audio_asset_id)
        if decision == "voiceover":
            scene.final_clip_asset_id = _mux_voiceover(ctx, scene, video, audio).id
            scene.lipsync_status = "voiceover"
            scene.status = "ready"
            continue
        # external lip-sync on (video, fitted speech)
        fitted = _fitted_audio(ctx, scene, video, audio)
        job = jobs.create_job(ctx.db, project_id=ctx.project.id, purpose="lipsync", kind="lipsync",
                              request={"video_key": video.storage_key, "audio_key": fitted.storage_key},
                              scene_id=scene.id, round=scene.regen_round,
                              idempotency_key=jobs.idem_key("lipsync", scene.id, video.id))
        if job.status == "succeeded":
            scene.final_clip_asset_id = job.output_asset_id
            scene.lipsync_status = "synced"
            scene.status = "ready"
        elif job.status in ("failed", "cancelled"):
            scene.final_clip_asset_id = _mux_voiceover(ctx, scene, video, audio).id
            scene.lipsync_status = "voiceover"
            scene.status = "ready"
        else:
            pending.append(job)
    if pending:
        ctx.db.flush()
        _kick(pending)
        ctx.project.stage_detail = f"Lip-syncing {len(pending)} scene(s)"
        return WAIT
    return DONE


def _fitted_audio(ctx: Ctx, scene: Scene, video: GeneratedAsset, audio: GeneratedAsset) -> GeneratedAsset:
    target = max(video.duration or scene.duration, 1.0)
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as td:
        src = jobs.local_copy(audio.storage_key)
        out, factor = ff.fit_audio(src, target, os.path.join(td, "fit.wav"))
        os.unlink(src)
        return jobs.store_file(ctx.db, out, project_id=ctx.project.id, kind="audio", mime="audio/wav",
                               meta={"derived_from": audio.id, "tempo_factor": factor, "scene": scene.id})


def _mux_voiceover(ctx: Ctx, scene: Scene, video: GeneratedAsset, audio: GeneratedAsset) -> GeneratedAsset:
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as td:
        v = jobs.local_copy(video.storage_key)
        a = jobs.local_copy(audio.storage_key)
        try:
            fitted, _ = ff.fit_audio(a, max(ff.probe(v).duration, 1.0), os.path.join(td, "fit.wav"))
            out = ff.mux_audio(v, fitted, os.path.join(td, "vo.mp4"))
            return jobs.store_file(ctx.db, out, project_id=ctx.project.id, kind="video", mime="video/mp4",
                                   meta={"derived_from": video.id, "voiceover": True, "scene": scene.id})
        finally:
            os.unlink(v)
            os.unlink(a)


# ---------------------------------------------------------------- 8 editing
def stage_editing(ctx: Ctx) -> str:
    product_asset = _product_image(ctx)
    research = _research(ctx)
    editor = VideoEditor()
    for concept in _selected_concepts(ctx):
        sb = _storyboard(ctx, concept)
        scenes = list(sb.scenes)
        if any(s.status != "ready" or not s.final_clip_asset_id for s in scenes):
            continue
        latest = ctx.db.scalar(select(Export).where(Export.concept_id == concept.id).order_by(Export.version.desc()))
        clip_ids = [s.final_clip_asset_id for s in scenes]
        if latest and (latest.edit_settings or {}).get("clip_ids") == clip_ids:
            continue  # nothing changed since the last export
        wd = tempfile.mkdtemp(dir=tmp_dir(), prefix="edit_")
        try:
            clips = []
            for s in scenes:
                a = ctx.db.get(GeneratedAsset, s.final_clip_asset_id)
                clips.append(SceneClip(path=jobs.local_copy(a.storage_key), dialogue=s.dialogue,
                                       planned_duration=s.duration,
                                       trim_speech_tail=s.lipsync_status == "native",
                                       overlay_product=bool(ctx.st.get("product_overlay", True)) and s.idx == len(scenes) - 1
                                       and product_asset is not None and not ctx.st.get("end_card", True)))
            music = None
            if ctx.st.get("music"):
                mj = ctx.db.scalar(select(GenerationJob).where(
                    GenerationJob.idempotency_key == jobs.idem_key("music", concept.id)))
                if mj and mj.status == "succeeded":
                    music = jobs.local_copy(ctx.db.get(GeneratedAsset, mj.output_asset_id).storage_key)
            settings = EditSettings(
                subtitles=bool(ctx.st.get("subtitles", True)), end_card=bool(ctx.st.get("end_card", True)),
                cta=concept.cta, brand=research.brand or research.product_name,
                product_image=jobs.local_copy(product_asset.storage_key) if product_asset else None,
                music_path=music)
            result = editor.assemble(clips, settings, workdir=wd)
            version = (latest.version + 1) if latest else 1
            if latest and latest.status == "draft":
                latest.status = "superseded"
            video = jobs.store_file(ctx.db, result.video_path, project_id=ctx.project.id, kind="export",
                                    mime="video/mp4", meta={"concept": concept.id, "version": version})
            thumb = jobs.store_file(ctx.db, result.thumbnail_path, project_id=ctx.project.id, kind="image",
                                    mime="image/jpeg", meta={"thumbnail_for": video.id})
            subs = jobs.store_file(ctx.db, result.srt_path, project_id=ctx.project.id, kind="subtitle",
                                   mime="application/x-subrip") if result.srt_path else None
            ctx.db.add(Export(project_id=ctx.project.id, concept_id=concept.id, version=version, status="draft",
                              asset_id=video.id, thumbnail_asset_id=thumb.id,
                              subtitles_asset_id=subs.id if subs else None, duration=result.duration,
                              width=video.width, height=video.height,
                              edit_settings={"clip_ids": clip_ids, "timeline": result.timeline,
                                             "subtitles": settings.subtitles, "end_card": settings.end_card,
                                             "music": bool(music)}))
        finally:
            shutil.rmtree(wd, ignore_errors=True)
    return DONE


# ---------------------------------------------------------------- 9 QA
def stage_qa(ctx: Ctx) -> str:
    s = get_settings()
    qa = QualityAssurance(registry.llm_provider(), registry.transcription_provider(), s.qa_identity_min_score)
    creator = _creator(ctx)
    anchor = ctx.db.get(GeneratedAsset, creator.anchor_asset_id)
    product_asset = _product_image(ctx)
    anchor_path = jobs.local_copy(anchor.storage_key)
    product_path = jobs.local_copy(product_asset.storage_key) if product_asset else None
    regen: list[Scene] = []
    try:
        for scene, sb, concept in _scenes(ctx):
            if scene.qa_status is not None or not scene.final_clip_asset_id:
                continue
            clip = jobs.local_copy(ctx.db.get(GeneratedAsset, scene.final_clip_asset_id).storage_key)
            try:
                r = qa.check_scene(clip=clip, dialogue=scene.dialogue, language=ctx.language,
                                   audio_source=scene.audio_source, lipsync_status=scene.lipsync_status,
                                   anchor_image=anchor_path, product_image=product_path,
                                   expects_product="product_image" in (scene.required_references or []))
            finally:
                os.unlink(clip)
            if r.usage:
                costs.record_llm_usage(ctx.db, ctx.project.id, r.usage, "scene_qa")
            ctx.db.add(QAReport(project_id=ctx.project.id, concept_id=concept.id, scene_id=scene.id, scope="scene",
                                round=scene.regen_round, passed=r.passed, score=r.score, checks=r.checks,
                                issues=r.issues))
            scene.qa_status = "passed" if r.passed else ("failed" if r.regenerable else "warning")
            if not r.passed and r.regenerable:
                regen.append(scene)
    finally:
        os.unlink(anchor_path)
        if product_path:
            os.unlink(product_path)

    # regenerate only failed scenes, within round + budget limits
    if regen and ctx.project.qa_round < s.max_qa_rounds:
        media = registry.media_provider()
        extra = sum(media.estimate_credits(video_producer.video_request(
            prompt=sc.video_prompt, duration=sc.duration, info=_video_info(ctx), keyframe_url=None,
            reference_urls=[], resolution=ctx.st.get("resolution") or s.letzai_video_resolution,
            native_audio=True)) for sc in regen)
        try:
            costs.check_budget(ctx.db, ctx.project, extra)
            ctx.project.qa_round += 1
            for sc in regen:
                sc.regen_round += 1
                sc.video_asset_id = None
                sc.final_clip_asset_id = None
                sc.lipsync_status = None
                sc.qa_status = None
                sc.status = "pending"
                if sc.audio_source == "native":
                    sc.audio_asset_id = None
            ctx.project.stage_detail = f"QA round {ctx.project.qa_round}: regenerating {len(regen)} scene(s)"
            return "goto:video"
        except costs.BudgetExceeded as e:
            ctx.project.stage_detail = f"QA regeneration skipped: {e}"

    # final export checks (latest export per concept)
    for concept in _selected_concepts(ctx):
        ex = ctx.db.scalar(select(Export).where(Export.concept_id == concept.id).order_by(Export.version.desc()))
        if not ex or ex.status != "draft":
            continue
        path = jobs.local_copy(ctx.db.get(GeneratedAsset, ex.asset_id).storage_key)
        try:
            r = qa.check_export(path, target_duration=concept.target_duration)
        finally:
            os.unlink(path)
        scene_reports = ctx.db.scalars(select(QAReport).join(Scene, QAReport.scene_id == Scene.id).where(
            QAReport.concept_id == concept.id, QAReport.scope == "scene",
            QAReport.round == Scene.regen_round)).all()
        scenes_ok = all(rep.passed for rep in scene_reports)
        ctx.db.add(QAReport(project_id=ctx.project.id, concept_id=concept.id, export_id=ex.id, scope="export",
                            round=ctx.project.qa_round, passed=r.passed and scenes_ok, checks=r.checks,
                            issues=r.issues + ([] if scenes_ok else [{"check": "scene_qa", "severity": "high",
                                                                      "detail": "one or more scenes failed QA"}])))
        ex.status = "approved" if (r.passed and scenes_ok) else "qa_failed"
    return DONE


# ---------------------------------------------------------------- 10 export
def stage_export(ctx: Ctx) -> str:
    exports = ctx.db.scalars(select(Export).where(Export.project_id == ctx.project.id)).all()
    latest: dict[str, Export] = {}
    for e in exports:
        if e.concept_id not in latest or e.version > latest[e.concept_id].version:
            latest[e.concept_id] = e
    if not latest:
        raise StageFailed("No advertisement could be assembled.")
    approved = [e for e in latest.values() if e.status == "approved"]
    ctx.project.stage_detail = (f"{len(approved)} of {len(latest)} advertisement(s) passed QA"
                                + ("" if len(approved) == len(latest) else "; review the QA report for the rest"))
    ctx.project.completed_at = utcnow()
    return DONE


STAGE_FUNCS = {"research": stage_research, "script": stage_script, "character": stage_character,
               "scenes": stage_scenes, "video": stage_video, "voice": stage_voice, "lipsync": stage_lipsync,
               "editing": stage_editing, "qa": stage_qa, "export": stage_export}
