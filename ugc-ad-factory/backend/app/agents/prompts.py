"""Prompt building blocks and compliance rules.

Realism / identity / dialogue directives are adapted (MIT) from
kofiowusuai-lab/ugc-skills (realism_prompts.md, ugc_character_bible.sh,
ugc_qa_bank.md) and rewritten for LetzAI's prompt guidance: concrete,
director-style details, no quality-tag padding.
"""
from __future__ import annotations

import re

WORDS_PER_SECOND = {"en": 2.5, "de": 2.2}

REALISM = (
    "Candid vertical 9:16 phone footage, shot on a smartphone front camera held slightly low and close. "
    "Natural unretouched skin with visible pores, slight under-eye shadows, a few flyaway hairs; "
    "no makeup gloss, no beautification. Soft window daylight with realistic dynamic range, "
    "slightly imperfect framing, mild lens distortion, deep focus without bokeh. "
    "Mundane real home setting. Not CGI, not 3D, not an illustration, no glamour look."
)

NO_TEXT = "No on-screen text, no captions, no watermark, no logos except those on the real product."

IDENTITY_LOCK = (
    "Use the first reference image as the IDENTITY REFERENCE. Keep this exact same person: same face "
    "shape, skin tone, hair, age and wardrobe. Photorealistic, not an illustration. "
    "Change only the following: "
)

PRODUCT_LOCK = (
    "The product must match the product reference image exactly: same shape, colours, packaging and label "
    "layout. Do not invent or alter any text, logo or branding on it."
)

ANIMATION = (
    "Subtle handheld micro-shake, natural blinks, small head tilts, eyebrow raises, subtle breathing, "
    "relaxed open hands, no finger counting. Eye contact with the lens."
)

FORBIDDEN_PROMPT_WORDS = ["masterpiece", "stunning", "gorgeous", "beautiful", "perfect", "epic",
                          "breathtaking", "award-winning", "ultra cinematic", "insanely detailed",
                          "best quality", "8k", "ultra-detailed", "viral", "trending"]


def clean_prompt(text: str) -> str:
    out = text
    for w in FORBIDDEN_PROMPT_WORDS:
        out = re.sub(rf"\b{re.escape(w)}\b", "", out, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", out).strip()


def dialogue_lock(dialogue: str, language: str) -> str:
    lang = "German" if language == "de" else "English"
    return (f'They speak in natural conversational {lang}, mouth clearly opening and closing on every '
            f'word, and say these EXACT words and nothing else: "{dialogue}". '
            "No greeting, no extra words, do not describe the background.")


def voiceover_direction() -> str:
    return ("They do not speak; natural reactions, small nods and expressions while demonstrating. "
            "Mouth mostly closed.")


def max_words(seconds: float, language: str) -> int:
    return max(3, int(seconds * WORDS_PER_SECOND.get(language, 2.5)))


# ---------------------------------------------------------------- compliance
FABRICATED_EXPERIENCE_PATTERNS = [
    r"\bI(?:'ve| have) been using\b", r"\bsince I started using\b", r"\bchanged my life\b",
    r"\bmy results\b", r"\bI lost \d", r"\bworked for me\b", r"\bI(?:'ve| have) tried everything\b",
    r"\bcustomers (?:say|love)\b", r"\breviews? (?:say|said)\b", r"\b\d(?:\.\d)? stars?\b", "★",
    r"\bich (?:benutze|nutze|verwende) (?:es |das |ihn |sie )?seit\b", r"\bseit ich\b.*\b(?:benutze|nutze)\b",
    r"\bhat mein leben\b", r"\bmeine ergebnisse\b", r"\bbei mir hat\b.*\bgeholfen\b",
    r"\bkunden (?:sagen|lieben)\b", r"\bbewertungen\b",
]


def fabricated_experience_flags(text: str) -> list[str]:
    """Phrases that present a fictional creator's personal experience or
    customer testimonials as fact. Scripts containing them are rejected."""
    hits = []
    for pat in FABRICATED_EXPERIENCE_PATTERNS:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            hits.append(m.group(0))
    return hits


RESEARCH_SYSTEM = """You are a meticulous product researcher for advertising.
Extract facts ONLY from the provided source material (page text, metadata, the user's description).
Never invent benefits, statistics, reviews, certifications or performance claims.
Every supported claim needs evidence quoted from the sources. Put anything uncertain, regulated
(health, finance, environmental) or exaggerated into claims_to_avoid.
before_after_supported is true only if the sources explicitly document a visible before/after result."""

STRATEGY_SYSTEM = """You are a direct-response UGC advertising strategist.
Write short vertical-video ad concepts spoken by a FICTIONAL creator to camera.
Rules:
- Use only the supported claims from the research; list the exact claims you rely on in claims_used.
- The creator is fictional: never fabricate personal experience, results, time-in-use, or customer
  testimonials/reviews. Use present-tense demonstration ("look at how…", "here's what it does") and
  second-person framing instead of "I've been using this for months".
- One clear claim per ad, a hook that lands in under 2.5 seconds, an honest tone, a clear CTA.
- Respect the spoken word budget given (≈2.5 words/second English, ≈2.2 German).
- When German is requested, write natural spoken German (casual "du", contractions like "hab'",
  "gibt's", short sentences, numbers written as words), not translated English.
- Only use the before_after angle if research.before_after_supported is true."""

CREATOR_SYSTEM = """You are a casting and creative director for UGC ads. Design a believable,
FICTIONAL everyday creator (not a celebrity, not a real person) that fits the product's audience.
Be concrete and visual: age range, appearance, clothing, home environment, camera position,
lighting, expressions, body language and voice. Avoid glamour; aim for relatable realism."""

SCENE_SYSTEM = """You are a scene director converting a UGC ad script into a shot-by-shot storyboard
for an AI video model. Keep the creator, wardrobe and setting consistent across scenes. Each scene is
one continuous shot with a single action. Prompts must read like director's notes: subject, action,
framing, camera, lens, lighting. Never ask the model to render logos or readable text; real product
imagery is composited in editing. Respect the per-scene duration limits and word budgets given."""

QA_SYSTEM = """You are a strict visual QA referee for AI-generated UGC ad footage. Compare frames of a
generated scene against the creator identity reference and (if provided) the real product image.
Score identity only on whether it is the same person: a different crop, angle, distance or lighting of
the same person must still score >= 0.85. Flag: different person, product shape/colour/label mismatch,
invented or garbled branding/text, malformed hands or fingers, warping/melting artifacts, extra limbs,
continuity breaks. Be specific and conservative; do not claim certainty you do not have."""
