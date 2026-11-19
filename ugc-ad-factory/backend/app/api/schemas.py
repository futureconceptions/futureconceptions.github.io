"""Request bodies (validated) and a few response shapes."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str | None = Field(default=None, max_length=200)
    role: Literal["admin", "member", "viewer"] = "member"


class CreatorPrefs(BaseModel):
    gender: Literal["female", "male", "any"] | None = None
    age_range: str | None = Field(default=None, max_length=20)
    appearance: str | None = Field(default=None, max_length=500)
    clothing: str | None = Field(default=None, max_length=300)
    environment: str | None = Field(default=None, max_length=300)


Checkpoint = Literal["concepts", "creator", "storyboard"]


class ProjectCreate(BaseModel):
    name: str | None = Field(default=None, max_length=200, description="Project label (not used in ads)")
    product_name: str | None = Field(default=None, max_length=200)
    product_url: HttpUrl | None = None
    product_description: str | None = Field(default=None, max_length=8000)
    brand_name: str | None = Field(default=None, max_length=200)
    brand_guidelines: str | None = Field(default=None, max_length=4000)
    target_audience: str | None = Field(default=None, max_length=500)
    language: Literal["en", "de"] = "en"
    duration: int = Field(default=20, ge=8, le=60)
    variants: int = Field(default=2, ge=1, le=5)
    cta: str | None = Field(default=None, max_length=120)
    creator_id: str | None = None
    creator_prefs: CreatorPrefs | None = None
    approval_checkpoints: list[Checkpoint] = []
    video_model: str | None = Field(default=None, max_length=100)
    image_model: str | None = Field(default=None, max_length=100)
    audio_mode: Literal["auto", "native", "tts"] = "auto"
    resolution: Literal["480p", "720p", "768p", "1080p"] | None = None
    video_candidates: int = Field(default=1, ge=1, le=3)
    anchor_candidates: int = Field(default=1, ge=1, le=4)
    keyframes: Literal["per_scene", "anchor_only"] = "per_scene"
    subtitles: bool = True
    end_card: bool = True
    music: bool = False
    budget_credits: int | None = Field(default=None, ge=0, le=10_000_000)
    confirm_budget: bool = False
    assets_licensed: bool = Field(default=False, description="User confirms rights to uploaded images")

    def pipeline_settings(self) -> dict:
        d = self.model_dump(exclude={"name", "product_name", "product_url", "product_description", "brand_name",
                                     "brand_guidelines", "creator_id", "budget_credits", "confirm_budget",
                                     "assets_licensed"})
        d["creator_prefs"] = (self.creator_prefs.model_dump(exclude_none=True) if self.creator_prefs else {})
        if d.get("audio_mode") == "auto":
            d.pop("audio_mode")
        return {k: v for k, v in d.items() if v is not None}


class ApproveRequest(BaseModel):
    checkpoint: Checkpoint
    selected_concept_ids: list[str] | None = None  # for the concepts checkpoint


class BudgetConfirm(BaseModel):
    budget_credits: int | None = Field(default=None, ge=0, le=10_000_000)


class CreatorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    appearance: dict = {}
    voice_preset: Literal["warm-narrator", "bright-host", "calm-guide", "deep-trailer", "crisp-news",
                          "friendly-young"] = "friendly-young"
    language: Literal["en", "de"] = "en"
    is_fictional: bool = True
    # Required when is_fictional is False (real person's likeness)
    consent_person_name: str | None = Field(default=None, max_length=200)
    consent_reference: str | None = Field(default=None, max_length=500)
    consent_confirmed: bool = False
    generate_anchor: bool = True

    @model_validator(mode="after")
    def _consent(self):
        if not self.is_fictional and not (self.consent_confirmed and self.consent_person_name and self.consent_reference):
            raise ValueError("Real-person likeness requires consent_person_name, consent_reference and consent_confirmed")
        return self


class SettingUpdate(BaseModel):
    value: dict | list | str | int | float | bool | None
