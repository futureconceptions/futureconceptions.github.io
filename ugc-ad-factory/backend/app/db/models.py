"""Relational model. IDs are UUID strings for portability (PostgreSQL in
production, SQLite in unit tests). Every external generation is a
GenerationJob row; every HTTP call to a provider is a ProviderRequest row;
every billable outcome is a UsageRecord row."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ts(**kw):
    return mapped_column(DateTime(timezone=True), default=utcnow, **kw)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    full_name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="member")  # admin|member|viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _ts()


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    # draft|queued|running|awaiting_approval|awaiting_budget|completed|failed|cancelled
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    stage: Mapped[str] = mapped_column(String(30), default="research")
    stage_detail: Mapped[str | None] = mapped_column(String(500))
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    creator_id: Mapped[str | None] = mapped_column(ForeignKey("creators.id", ondelete="SET NULL"))
    budget_credits: Mapped[int] = mapped_column(Integer, default=20000)
    estimated_credits: Mapped[int] = mapped_column(Integer, default=0)
    budget_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    approvals: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    qa_round: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    lease_owner: Mapped[str | None] = mapped_column(String(64))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _ts()
    updated_at: Mapped[datetime] = _ts(onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped["Product | None"] = relationship(back_populates="project", uselist=False,
                                                       cascade="all, delete-orphan")
    concepts: Mapped[list["AdConcept"]] = relationship(back_populates="project",
                                                       cascade="all, delete-orphan",
                                                       order_by="AdConcept.rank")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                            unique=True)
    url: Mapped[str | None] = mapped_column(String(2000))
    name: Mapped[str | None] = mapped_column(String(300))
    brand_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    brand_guidelines: Mapped[str | None] = mapped_column(Text)
    page_text: Mapped[str | None] = mapped_column(Text)
    page_meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    fetch_status: Mapped[str | None] = mapped_column(String(60))  # ok|robots_disallowed|error|skipped
    research: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = _ts()

    project: Mapped[Project] = relationship(back_populates="product")
    assets: Mapped[list["ProductAsset"]] = relationship(back_populates="product",
                                                        cascade="all, delete-orphan")


class ProductAsset(Base):
    __tablename__ = "product_assets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"),
                                            index=True)
    kind: Mapped[str] = mapped_column(String(30), default="image")  # image|screenshot|logo
    storage_key: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    filename: Mapped[str | None] = mapped_column(String(300))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    provider_url: Mapped[str | None] = mapped_column(String(2000))  # uploaded copy at LetzAI
    license_note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = _ts()

    product: Mapped[Product] = relationship(back_populates="assets")


class Creator(Base):
    __tablename__ = "creators"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    appearance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    voice: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|generating|ready|approved|failed
    is_fictional: Mapped[bool] = mapped_column(Boolean, default=True)
    # Required when is_fictional is False: who consented, how, reference to evidence.
    likeness_consent: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    anchor_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("generated_assets.id", ondelete="SET NULL", use_alter=True,
                   name="fk_creator_anchor_asset"))
    anchor_prompt: Mapped[str | None] = mapped_column(Text)
    generation_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = _ts()
    updated_at: Mapped[datetime] = _ts(onupdate=utcnow)

    references: Mapped[list["CreatorReference"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan")


class CreatorReference(Base):
    __tablename__ = "creator_references"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    creator_id: Mapped[str] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"),
                                            index=True)
    kind: Mapped[str] = mapped_column(String(20), default="anchor")  # anchor|variant|uploaded
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                            ondelete="SET NULL"))
    storage_key: Mapped[str | None] = mapped_column(String(500))
    provider_url: Mapped[str | None] = mapped_column(String(2000))
    prompt: Mapped[str | None] = mapped_column(Text)
    identity_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = _ts()

    creator: Mapped[Creator] = relationship(back_populates="references")


class AdConcept(Base):
    __tablename__ = "ad_concepts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                            index=True)
    angle: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(300))
    hook: Mapped[str] = mapped_column(Text)
    core_message: Mapped[str] = mapped_column(Text)
    emotional_angle: Mapped[str | None] = mapped_column(String(300))
    visual_concept: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(String(300))
    target_duration: Mapped[int] = mapped_column(Integer, default=20)
    claims_used: Mapped[list[str]] = mapped_column(JSON, default=list)
    score: Mapped[float] = mapped_column(Float, default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _ts()

    project: Mapped[Project] = relationship(back_populates="concepts")
    scripts: Mapped[list["Script"]] = relationship(back_populates="concept",
                                                   cascade="all, delete-orphan",
                                                   order_by="Script.version")


class Script(Base):
    __tablename__ = "scripts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("ad_concepts.id", ondelete="CASCADE"),
                                            index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    language: Mapped[str] = mapped_column(String(10), default="en")
    full_text: Mapped[str] = mapped_column(Text)
    beats: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = _ts()

    concept: Mapped[AdConcept] = relationship(back_populates="scripts")
    __table_args__ = (UniqueConstraint("concept_id", "version"),)


class Storyboard(Base):
    __tablename__ = "storyboards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("ad_concepts.id", ondelete="CASCADE"),
                                            index=True)
    script_id: Mapped[str] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    video_model: Mapped[str | None] = mapped_column(String(100))
    audio_mode: Mapped[str] = mapped_column(String(20), default="native")  # native|tts
    total_duration: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _ts()

    scenes: Mapped[list["Scene"]] = relationship(back_populates="storyboard",
                                                 cascade="all, delete-orphan",
                                                 order_by="Scene.idx")


class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    storyboard_id: Mapped[str] = mapped_column(ForeignKey("storyboards.id", ondelete="CASCADE"),
                                               index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                            index=True)
    idx: Mapped[int] = mapped_column(Integer)
    beat: Mapped[str | None] = mapped_column(String(40))
    duration: Mapped[float] = mapped_column(Float)
    dialogue: Mapped[str] = mapped_column(Text, default="")
    framing: Mapped[str | None] = mapped_column(String(300))
    creator_movement: Mapped[str | None] = mapped_column(String(500))
    product_interaction: Mapped[str | None] = mapped_column(String(500))
    environment: Mapped[str | None] = mapped_column(String(500))
    required_references: Mapped[list[str]] = mapped_column(JSON, default=list)
    keyframe_prompt: Mapped[str | None] = mapped_column(Text)
    video_prompt: Mapped[str] = mapped_column(Text, default="")
    audio_requirements: Mapped[str | None] = mapped_column(String(500))
    overlay_text: Mapped[str | None] = mapped_column(String(300))
    # pending|keyframe|video|voice|lipsync|ready|failed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    regen_round: Mapped[int] = mapped_column(Integer, default=0)
    audio_source: Mapped[str | None] = mapped_column(String(20))  # native|tts|none
    keyframe_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                     ondelete="SET NULL"))
    video_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                  ondelete="SET NULL"))
    audio_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                  ondelete="SET NULL"))
    final_clip_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                       ondelete="SET NULL"))
    lipsync_status: Mapped[str | None] = mapped_column(String(30))  # native|synced|voiceover|skipped
    qa_status: Mapped[str | None] = mapped_column(String(20))  # passed|failed|warning
    created_at: Mapped[datetime] = _ts()

    storyboard: Mapped[Storyboard] = relationship(back_populates="scenes")
    __table_args__ = (UniqueConstraint("storyboard_id", "idx"),)


class GeneratedAsset(Base):
    __tablename__ = "generated_assets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                                   index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("generation_jobs.id",
                                                          ondelete="SET NULL",
                                                          use_alter=True,
                                                          name="fk_asset_job"))
    kind: Mapped[str] = mapped_column(String(20))  # image|video|audio|export|frame|subtitle
    storage_key: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration: Mapped[float | None] = mapped_column(Float)
    sha256: Mapped[str | None] = mapped_column(String(64))
    provider_url: Mapped[str | None] = mapped_column(String(2000))
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = _ts()


class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                                   index=True)
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"),
                                                 index=True)
    creator_id: Mapped[str | None] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(30))  # anchor|keyframe|scene_video|speech|lipsync
    kind: Mapped[str] = mapped_column(String(20))  # image|image_edit|video|speech|lipsync
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(100))
    # pending|submitted|running|succeeded|failed|cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(300), unique=True)
    candidate_index: Mapped[int] = mapped_column(Integer, default=0)
    round: Mapped[int] = mapped_column(Integer, default=0)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provider_job_id: Mapped[str | None] = mapped_column(String(100), index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    poll_errors: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    estimated_credits: Mapped[float] = mapped_column(Float, default=0)
    actual_credits: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)
    output_url: Mapped[str | None] = mapped_column(String(2000))
    output_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                   ondelete="SET NULL"))
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _ts()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_poll_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = _ts(onupdate=utcnow)

    __table_args__ = (Index("ix_jobs_provider_status", "provider", "status"),)


class ProviderRequest(Base):
    __tablename__ = "provider_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("generation_jobs.id",
                                                          ondelete="SET NULL"), index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                                   index=True)
    provider: Mapped[str] = mapped_column(String(40))
    operation: Mapped[str] = mapped_column(String(60))
    method: Mapped[str | None] = mapped_column(String(10))
    endpoint: Mapped[str | None] = mapped_column(String(500))
    status_code: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    request_excerpt: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    response_excerpt: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _ts()


class QAReport(Base):
    __tablename__ = "qa_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                            index=True)
    concept_id: Mapped[str | None] = mapped_column(ForeignKey("ad_concepts.id",
                                                              ondelete="CASCADE"))
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"))
    export_id: Mapped[str | None] = mapped_column(ForeignKey("exports.id", ondelete="CASCADE"))
    scope: Mapped[str] = mapped_column(String(20))  # scene|export
    round: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float)
    checks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = _ts()


class Export(Base):
    __tablename__ = "exports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                                            index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("ad_concepts.id", ondelete="CASCADE"),
                                            index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|approved|qa_failed
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                            ondelete="SET NULL"))
    thumbnail_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                      ondelete="SET NULL"))
    subtitles_asset_id: Mapped[str | None] = mapped_column(ForeignKey("generated_assets.id",
                                                                      ondelete="SET NULL"))
    duration: Mapped[float | None] = mapped_column(Float)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    edit_settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = _ts()

    __table_args__ = (UniqueConstraint("concept_id", "version"),)


class UsageRecord(Base):
    __tablename__ = "usage_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"),
                                                   index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("generation_jobs.id",
                                                          ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(30))
    units: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str | None] = mapped_column(String(30))
    credits: Mapped[float] = mapped_column(Float, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _ts(index=True)


class ApplicationSetting(Base):
    __tablename__ = "application_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = _ts(onupdate=utcnow)
