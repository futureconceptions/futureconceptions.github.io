"""Agent 4 - Scene Director: script beats -> storyboard within model limits."""
from __future__ import annotations

from app.agents import prompts as P
from app.agents.schemas import Beat, SceneSpec, StoryboardPlan
from app.providers.base import LLMUsage, VideoModelInfo


def heuristic_storyboard(beats: list[Beat], creator: dict, product_name: str, has_product: bool) -> StoryboardPlan:
    framings = {"hook": "medium close-up, chest-up selfie framing", "cta": "medium shot, product held next to face",
                "demo": "close-up on hands and product with face in frame", "cta_default": "medium shot"}
    scenes = []
    for b in beats:
        prod = has_product and b.beat in ("hook", "demo", "proof", "mechanism", "cta", "objection", "problem")
        scenes.append(SceneSpec(
            beat=b.beat, duration=b.seconds, dialogue=b.dialogue,
            framing=framings.get(b.beat, "medium close-up selfie framing"),
            creator_movement=b.on_screen_action,
            product_interaction=f"holds {product_name} naturally toward the camera" if prod else "none",
            environment=creator.get("environment", "home interior"),
            needs_product_reference=prod,
            keyframe_prompt=f"{b.on_screen_action}, {framings.get(b.beat, 'medium close-up')}",
            video_prompt=f"{b.on_screen_action}. Camera stays on the creator, {framings.get(b.beat, 'medium close-up')}.",
            audio_requirements="clear close-mic speech, quiet room tone",
            overlay_text=None))
    return StoryboardPlan(scenes=scenes, notes="Template storyboard (offline mode): one shot per beat.")


def fit_to_model(scenes: list[SceneSpec], info: VideoModelInfo, language: str) -> list[SceneSpec]:
    """Merge scenes shorter than the model minimum into their neighbour and
    split scenes longer than the maximum; then enforce the word budget."""
    pref_max = min(info.max_duration, max(info.min_duration, 10))
    merged: list[SceneSpec] = []
    for sc in scenes:
        if merged and (merged[-1].duration < info.min_duration or sc.duration < info.min_duration) \
                and merged[-1].duration + sc.duration <= pref_max:
            prev = merged[-1]
            merged[-1] = prev.model_copy(update={
                "beat": f"{prev.beat}+{sc.beat}", "duration": prev.duration + sc.duration,
                "dialogue": f"{prev.dialogue} {sc.dialogue}".strip(),
                "creator_movement": f"{prev.creator_movement}; then {sc.creator_movement}",
                "needs_product_reference": prev.needs_product_reference or sc.needs_product_reference,
                "product_interaction": sc.product_interaction if sc.product_interaction != "none" else prev.product_interaction,
                "video_prompt": f"{prev.video_prompt} Then: {sc.video_prompt}"})
        else:
            merged.append(sc)
    # second pass: anything still below the minimum merges if the model max allows, else is extended
    i = 0
    while i < len(merged):
        sc = merged[i]
        if sc.duration < info.min_duration:
            nxt = merged[i + 1] if i + 1 < len(merged) else None
            if nxt and sc.duration + nxt.duration <= info.max_duration:
                merged[i] = sc.model_copy(update={
                    "beat": f"{sc.beat}+{nxt.beat}", "duration": sc.duration + nxt.duration,
                    "dialogue": f"{sc.dialogue} {nxt.dialogue}".strip(),
                    "needs_product_reference": sc.needs_product_reference or nxt.needs_product_reference,
                    "video_prompt": f"{sc.video_prompt} Then: {nxt.video_prompt}"})
                del merged[i + 1]
                continue
            merged[i] = sc.model_copy(update={"duration": float(info.min_duration)})
        i += 1
    out: list[SceneSpec] = []
    for sc in merged:
        if sc.duration > info.max_duration:
            n = int(-(-sc.duration // info.max_duration))
            words = sc.dialogue.split()
            per = -(-len(words) // n) if words else 0
            for i in range(n):
                out.append(sc.model_copy(update={"duration": sc.duration / n,
                                                 "dialogue": " ".join(words[i * per:(i + 1) * per])}))
        else:
            out.append(sc)
    for i, sc in enumerate(out):
        budget = P.max_words(sc.duration, language)
        words = sc.dialogue.split()
        if len(words) > budget:
            # extend the scene if the model allows, otherwise trim dialogue
            need = len(words) / P.WORDS_PER_SECOND.get(language, 2.5)
            if need <= info.max_duration:
                out[i] = sc.model_copy(update={"duration": round(need + 0.3, 1)})
            else:
                out[i] = sc.model_copy(update={"dialogue": " ".join(words[:budget])})
    return out


def compose_prompts(sc: SceneSpec, creator: dict, language: str, audio_mode: str) -> tuple[str, str]:
    """Deterministic final prompts: identity/product/dialogue locks are always present."""
    keyframe = P.clean_prompt(
        P.IDENTITY_LOCK + f"{sc.keyframe_prompt}. Framing: {sc.framing}. Setting: {sc.environment}. "
        + (f"Product interaction: {sc.product_interaction}. {P.PRODUCT_LOCK} " if sc.needs_product_reference else "")
        + f"{creator.get('lighting', '')}. {P.REALISM} {P.NO_TEXT}")
    speech = P.dialogue_lock(sc.dialogue, language) if (audio_mode == "native" and sc.dialogue) else P.voiceover_direction()
    video = P.clean_prompt(
        f"Continue from this exact source image as the first frame: same person, same wardrobe, same setting. "
        f"{sc.video_prompt} Framing: {sc.framing}. {P.ANIMATION} {speech} {P.NO_TEXT}")
    return keyframe, video


class SceneDirector:
    def __init__(self, llm):
        self.llm = llm

    def plan(self, *, beats: list[Beat], concept_title: str, creator: dict, product_name: str,
             has_product_images: bool, info: VideoModelInfo, language: str,
             audio_mode: str) -> tuple[list[SceneSpec], str, LLMUsage]:
        prompt = (f"Concept: {concept_title}\nCreator: {creator}\nProduct: {product_name} "
                  f"(real product photos available: {has_product_images})\n"
                  f"Video model: {info.display_name}; each scene must be {info.min_duration}-{info.max_duration}s.\n"
                  f"Audio: {'spoken on camera (native model audio)' if audio_mode == 'native' else 'voice-over added later; creator does not speak on camera'}.\n"
                  f"Language: {language}. Max ~{P.WORDS_PER_SECOND.get(language, 2.5)} words per second of dialogue.\n"
                  f"Script beats:\n" + "\n".join(f"- [{b.beat}] {b.seconds}s: \"{b.dialogue}\" / action: {b.on_screen_action}"
                                                 for b in beats))
        plan, usage = self.llm.structured(
            system=P.SCENE_SYSTEM, prompt=prompt, schema=StoryboardPlan, task="storyboard",
            fallback=lambda: heuristic_storyboard(beats, creator, product_name, has_product_images))
        scenes = fit_to_model(plan.scenes, info, language)
        return scenes, plan.notes, usage
