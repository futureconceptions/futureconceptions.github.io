"""Structured outputs for every agent (used as LLM output schemas and stored as JSON)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Angle = Literal["problem_solution", "product_demo", "educational", "before_after",
                "everyday_situation", "objection_handling", "product_discovery"]
Severity = Literal["low", "medium", "high", "critical"]


class SupportedClaim(BaseModel):
    claim: str
    evidence: str = Field(description="Exact sentence copied verbatim from an evidence passage (it is checked)")
    source: str = Field(description="'product_page', 'user_description' or 'product_images'")
    source_ref: str | None = Field(default=None, description="Evidence passage reference, e.g. d2#120:480")
    source_url: str | None = None


class ProductResearch(BaseModel):
    product_name: str
    brand: str | None = None
    category: str
    summary: str
    features: list[str]
    benefits: list[str]
    target_audience: list[str]
    customer_problems: list[str]
    differentiators: list[str]
    supported_claims: list[SupportedClaim]
    claims_to_avoid: list[str] = Field(description="Claims that would be unsupported, risky or regulated")
    potential_objections: list[str]
    price: str | None = None
    before_after_supported: bool = Field(
        description="True only if the source material explicitly documents a visible before/after result")
    language: str = "en"


class ResearchRecord(ProductResearch):
    """Stored research: the LLM output plus system-filled provenance."""
    sources: list[dict] = Field(default_factory=list)
    search: dict = Field(default_factory=dict)


class Beat(BaseModel):
    beat: Literal["hook", "problem", "demo", "mechanism", "proof", "objection", "cta"]
    dialogue: str
    on_screen_action: str
    seconds: float


class ConceptDraft(BaseModel):
    angle: Angle
    title: str
    hook: str
    core_message: str
    emotional_angle: str
    visual_concept: str
    cta: str
    target_duration: int
    beats: list[Beat]
    claims_used: list[str] = Field(description="Exact supported_claims[].claim strings this script relies on")
    self_score: float = Field(description="0-10 expected conversion strength")
    rationale: str


class ConceptSet(BaseModel):
    concepts: list[ConceptDraft]


class CreatorSpec(BaseModel):
    name: str
    age_range: str
    gender_presentation: str
    appearance: str
    clothing: str
    environment: str
    camera_positioning: str
    lighting: str
    facial_expressions: str
    body_language: str
    voice_characteristics: str
    voice_preset: Literal["warm-narrator", "bright-host", "calm-guide", "deep-trailer",
                          "crisp-news", "friendly-young"]


class SceneSpec(BaseModel):
    beat: str
    duration: float
    dialogue: str
    framing: str
    creator_movement: str
    product_interaction: str
    environment: str
    needs_product_reference: bool
    keyframe_prompt: str
    video_prompt: str
    audio_requirements: str
    overlay_text: str | None = None


class StoryboardPlan(BaseModel):
    scenes: list[SceneSpec]
    notes: str = ""


class QAIssue(BaseModel):
    check: str
    severity: Severity
    detail: str


class SceneVisualQA(BaseModel):
    identity_match: bool
    identity_score: float = Field(description="0-1; same person despite crop/angle/lighting must score >= 0.85")
    product_accuracy: Literal["ok", "mismatch", "not_visible", "not_applicable"]
    invented_branding: bool
    hand_anatomy_ok: bool
    visual_artifacts: bool
    continuity_ok: bool
    issues: list[QAIssue]
    overall_score: float = Field(description="0-1")
