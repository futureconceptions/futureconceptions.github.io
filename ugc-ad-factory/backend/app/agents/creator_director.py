"""Agent 3 - Creator Director: fictional creator design + anchor prompt."""
from __future__ import annotations

import hashlib

from app.agents import prompts as P
from app.agents.schemas import CreatorSpec, ProductResearch
from app.providers.base import LLMUsage

_FIRST = {"female": ["Lena", "Mara", "Sofia", "Jana", "Nora"], "male": ["Jonas", "Felix", "Ben", "Tim", "Leon"],
          "any": ["Alex", "Sam", "Robin", "Kim", "Charlie"]}


def heuristic_creator(research: ProductResearch, prefs: dict) -> CreatorSpec:
    gender = (prefs.get("gender") or "female").lower()
    gender = gender if gender in _FIRST else "any"
    seed = int(hashlib.md5(research.product_name.encode()).hexdigest()[:4], 16)
    age = prefs.get("age_range") or "25-34"
    voice = "friendly-young" if gender == "female" else ("warm-narrator" if gender == "male" else "bright-host")
    return CreatorSpec(
        name=_FIRST[gender][seed % 5],
        age_range=age,
        gender_presentation=gender if gender != "any" else "androgynous",
        appearance=prefs.get("appearance") or f"approachable {gender if gender != 'any' else 'person'} in their {age}, "
                                               "natural shoulder-length brown hair, light freckles, no heavy makeup",
        clothing=prefs.get("clothing") or "soft oatmeal knit sweater over a plain white t-shirt",
        environment=prefs.get("environment") or "bright, slightly lived-in apartment kitchen with plants and a wooden counter",
        camera_positioning="phone held at arm's length slightly below eye level, vertical framing chest-up",
        lighting="soft daylight from a window camera-left",
        facial_expressions="genuine, relaxed smile, curious eyebrow raises",
        body_language="leans toward the lens when making a point, open hand gestures",
        voice_characteristics="warm, conversational, medium pace",
        voice_preset=voice)


def anchor_prompt(spec: CreatorSpec) -> str:
    return P.clean_prompt(
        f"Portrait of a fictional person: {spec.gender_presentation}, age {spec.age_range}, {spec.appearance}. "
        f"Wearing {spec.clothing}. In {spec.environment}. {spec.camera_positioning}. {spec.lighting}. "
        f"Expression: {spec.facial_expressions}. Looking directly into the lens, neutral relaxed pose, hands "
        f"out of frame. {P.REALISM} {P.NO_TEXT}")


class CreatorDirector:
    def __init__(self, llm):
        self.llm = llm

    def design(self, research: ProductResearch, prefs: dict, language: str) -> tuple[CreatorSpec, LLMUsage]:
        prompt = (f"Product: {research.product_name} ({research.category}). Audience: {research.target_audience}.\n"
                  f"User preferences for the creator (may be empty): {prefs}.\n"
                  f"The ad is spoken in {'German' if language == 'de' else 'English'}; choose a fitting voice_preset.")
        return self.llm.structured(system=P.CREATOR_SYSTEM, prompt=prompt, schema=CreatorSpec,
                                   task="creator_design", fallback=lambda: heuristic_creator(research, prefs))
