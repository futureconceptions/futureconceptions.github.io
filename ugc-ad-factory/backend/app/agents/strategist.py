"""Agent 2 - Advertising Strategist: concepts + scripts, validation and selection."""
from __future__ import annotations

from dataclasses import dataclass

from app.agents import prompts as P
from app.agents.schemas import Beat, ConceptDraft, ConceptSet, ProductResearch
from app.providers.base import LLMUsage

DEFAULT_ANGLES = ["problem_solution", "product_demo", "everyday_situation", "objection_handling",
                  "educational", "product_discovery"]

_T = {
    "en": {
        "problem_solution": ("Still dealing with {problem}?", "Here's {product}: {claim}.", "Try it yourself."),
        "product_demo": ("Let me show you what {product} actually does.", "{claim}.", "See it for yourself."),
        "everyday_situation": ("You know that moment when {problem}?", "That's where {product} comes in. {claim}.", "Worth a look."),
        "objection_handling": ("Is {product} worth it? Fair question.", "{claim}. {claim2}.", "Decide for yourself."),
        "educational": ("Quick thing most people don't know about {category}.", "{claim}. That's what {product} is built around.", "Learn more."),
        "product_discovery": ("Okay, look what I just found.", "{product}. {claim}.", "Check it out."),
        "problem": "this everyday hassle",
    },
    "de": {
        "problem_solution": ("Kennst du das Problem mit {problem}?", "Schau dir {product} an: {claim}.", "Probier's selbst aus."),
        "product_demo": ("Ich zeig dir kurz, was {product} wirklich kann.", "{claim}.", "Überzeug dich selbst."),
        "everyday_situation": ("Du kennst diesen Moment, wenn {problem}?", "Genau dafür gibt's {product}. {claim}.", "Schau's dir an."),
        "objection_handling": ("Lohnt sich {product}? Gute Frage.", "{claim}. {claim2}.", "Entscheide selbst."),
        "educational": ("Kurz was, das kaum jemand über {category} weiß.", "{claim}. Genau darauf setzt {product}.", "Mehr erfahren."),
        "product_discovery": ("Okay, schau mal, was ich gefunden hab.", "{product}. {claim}.", "Schau's dir an."),
        "problem": "diesem Alltagsproblem",
    },
}


def _trim_words(text: str, n: int) -> str:
    words = text.split()
    return text if len(words) <= n else " ".join(words[:n]).rstrip(",;:") + "."


def heuristic_concepts(research: ProductResearch, *, language: str, duration: int, count: int,
                       cta: str | None, angles: list[str]) -> ConceptSet:
    lang = language if language in _T else "en"
    t = _T[lang]
    claims = [c.claim.rstrip(".") for c in research.supported_claims] or [research.summary.rstrip(".")]
    problem = (research.customer_problems[0] if research.customer_problems else t["problem"]).rstrip(".?")
    out = []
    for i, angle in enumerate(angles[:count]):
        hook_t, body_t, cta_default = t[angle]
        c1, c2 = claims[i % len(claims)], claims[(i + 1) % len(claims)]
        fmt = dict(product=research.product_name, claim=c1, claim2=c2, problem=problem,
                   category=research.category)
        hook = hook_t.format(**fmt)
        body = body_t.format(**fmt)
        cta_line = cta or cta_default
        budget = P.max_words(duration, lang)
        hook_s = min(3.0, max(2.0, len(hook.split()) / P.WORDS_PER_SECOND[lang]))
        cta_s = max(2.0, len(cta_line.split()) / P.WORDS_PER_SECOND[lang] + 0.5)
        body_s = max(3.0, duration - hook_s - cta_s)
        body = _trim_words(body, max(4, budget - len(hook.split()) - len(cta_line.split())))
        beats = [Beat(beat="hook", dialogue=hook, on_screen_action="creator looks into the lens, holds up the product", seconds=hook_s),
                 Beat(beat="demo", dialogue=body, on_screen_action="creator demonstrates the product close to camera", seconds=body_s),
                 Beat(beat="cta", dialogue=cta_line, on_screen_action="creator smiles and points toward the product", seconds=cta_s)]
        out.append(ConceptDraft(
            angle=angle, title=f"{angle.replace('_', ' ').title()} – {research.product_name}", hook=hook,
            core_message=c1, emotional_angle="curiosity and relief", visual_concept="selfie-style talking head at home with product in hand",
            cta=cta_line, target_duration=duration, beats=beats, claims_used=[c1] + ([c2] if "{claim2}" in body_t else []),
            self_score=7.0 - i * 0.3, rationale="Template concept built from verbatim supported claims (offline mode)."))
    return ConceptSet(concepts=out)


@dataclass
class ValidatedConcept:
    draft: ConceptDraft
    score: float
    problems: list[str]

    @property
    def valid(self) -> bool:
        return not any(p.startswith("REJECT") for p in self.problems)


def validate_concept(c: ConceptDraft, research: ProductResearch, language: str) -> ValidatedConcept:
    problems: list[str] = []
    full = " ".join(b.dialogue for b in c.beats)
    flags = P.fabricated_experience_flags(full)
    if flags:
        problems.append(f"REJECT fabricated experience/testimonial phrasing: {flags}")
    if c.angle == "before_after" and not research.before_after_supported:
        problems.append("REJECT before/after angle without documented support")
    supported = {s.claim.strip().lower() for s in research.supported_claims}
    unknown = [cl for cl in c.claims_used if cl.strip().lower() not in supported]
    if unknown and supported:
        problems.append(f"unverified claims referenced: {unknown}")
    words = len(full.split())
    budget = P.max_words(c.target_duration, language)
    if words > budget * 1.15:
        problems.append(f"over word budget ({words}>{budget})")
    if not c.cta.strip():
        problems.append("missing CTA")
    score = float(c.self_score) - 2.0 * len(unknown) - (1.5 if words > budget * 1.15 else 0)
    return ValidatedConcept(c, score, problems)


def select_concepts(validated: list[ValidatedConcept], n: int) -> list[ValidatedConcept]:
    """Highest score first, preferring distinct angles."""
    ok = sorted([v for v in validated if v.valid], key=lambda v: v.score, reverse=True)
    chosen, angles = [], set()
    for v in ok:
        if v.draft.angle not in angles:
            chosen.append(v)
            angles.add(v.draft.angle)
        if len(chosen) == n:
            return chosen
    for v in ok:
        if v not in chosen:
            chosen.append(v)
        if len(chosen) == n:
            break
    return chosen


class AdvertisingStrategist:
    def __init__(self, llm):
        self.llm = llm

    def run(self, research: ProductResearch, *, language: str, duration: int, variants: int,
            cta: str | None, audience: str | None, brand_guidelines: str | None,
            angles: list[str] | None = None) -> tuple[list[ValidatedConcept], list[ValidatedConcept], LLMUsage]:
        angles = angles or DEFAULT_ANGLES
        if research.before_after_supported and "before_after" not in angles:
            angles = angles + ["before_after"]
        count = min(len(angles), variants + 2)
        prompt = (f"RESEARCH JSON:\n{research.model_dump_json(indent=1)}\n\n"
                  f"Write {count} concepts, each a different angle from: {angles[:count]}.\n"
                  f"Language: {'German' if language == 'de' else 'English'}. Target duration: {duration}s "
                  f"(spoken budget ≈ {P.max_words(duration, language)} words total).\n"
                  f"Target audience: {audience or ', '.join(research.target_audience)}.\n"
                  f"Required CTA (use verbatim if given): {cta or 'choose an appropriate one'}.\n"
                  f"Brand guidelines: {brand_guidelines or 'none provided'}.\n"
                  "Beats must sum to the target duration. Keep each beat's dialogue speakable in its seconds.")
        cset, usage = self.llm.structured(
            system=P.STRATEGY_SYSTEM, prompt=prompt, schema=ConceptSet, task="ad_strategy",
            fallback=lambda: heuristic_concepts(research, language=language, duration=duration,
                                                count=count, cta=cta, angles=angles))
        validated = [validate_concept(c, research, language) for c in cset.concepts]
        return validated, select_concepts(validated, variants), usage
