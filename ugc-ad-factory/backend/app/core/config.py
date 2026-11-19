"""Application settings. Every secret comes from the environment (or a secret
manager that injects environment variables) - never from code or the frontend."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    # --- general ---
    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "UGC Ad Factory"
    log_level: str = "INFO"
    secret_key: SecretStr = SecretStr("change-me-in-production-please-32+chars")
    access_token_ttl_minutes: int = 60 * 12
    signed_url_ttl_seconds: int = 3600
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Bootstrap admin (created on startup if no user exists)
    bootstrap_admin_email: str | None = "admin@example.com"
    bootstrap_admin_password: SecretStr | None = SecretStr("admin12345")

    # --- database / queue ---
    database_url: str = "postgresql+psycopg://ugc:ugc@localhost:5432/ugc"
    redis_url: str = "redis://localhost:6379/0"
    # "celery" in deployments; "inline" runs tasks synchronously (tests / single-process dev)
    task_dispatch: Literal["celery", "inline"] = "celery"

    # --- storage ---
    storage_backend: Literal["s3", "local"] = "s3"
    local_storage_dir: str = "./data/storage"
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_public_endpoint_url: str | None = None  # endpoint browsers can reach (presigned URLs)
    s3_region: str = "us-east-1"
    s3_bucket: str = "ugc-assets"
    s3_access_key: SecretStr = SecretStr("minioadmin")
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    public_api_url: str = "http://localhost:8000"  # used to build signed local-file URLs

    # --- providers ---
    # "mock" generates real local media with FFmpeg and never calls paid APIs.
    media_provider: Literal["letzai", "mock"] = "mock"
    llm_provider: Literal["anthropic", "heuristic"] = "heuristic"
    lipsync_provider: Literal["none", "wavespeed", "mock"] = "none"
    transcription_provider: Literal["none", "faster_whisper"] = "none"

    letzai_api_key: SecretStr | None = None
    letzai_base_url: str = "https://api.letz.ai"
    letzai_organization_id: str | None = None
    letzai_catalog_ttl_seconds: int = 3600
    letzai_image_model: str = "gemini-3-pro-image"
    letzai_edit_model: str = "gemini-3-pro-image"
    letzai_video_model: str = "video-seedance25"
    letzai_speech_model: str = "audio-eleven-v4"
    letzai_video_resolution: str = "720p"
    letzai_has_watermark: bool = False
    letzai_max_concurrent_jobs: int = 4
    # Optional conversion for display; credits are always the source of truth.
    letzai_usd_per_credit: float | None = None
    # Base URL LetzAI can reach for webhooks (e.g. https://ads.example.com). Empty = poll only.
    webhook_base_url: str | None = None

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_fallback_model: str | None = "claude-opus-4-8"
    anthropic_usd_per_mtok_in: float = 4.0
    anthropic_usd_per_mtok_out: float = 20.0

    wavespeed_api_key: SecretStr | None = None
    wavespeed_model: str = "sync/lipsync-2"

    # --- pipeline defaults ---
    default_video_candidates: int = 1
    max_job_attempts: int = 3
    max_qa_rounds: int = 2
    qa_identity_min_score: float = 0.80
    default_project_budget_credits: int = 20000
    global_budget_credits: int = 500000
    poll_interval_seconds: int = 5
    poll_timeout_seconds: int = 60 * 30

    # --- url fetching ---
    fetch_timeout_seconds: float = 15.0
    fetch_max_bytes: int = 5_000_000
    fetch_user_agent: str = "UGCAdFactoryBot/1.0 (+product research; respects robots.txt)"
    fetch_allow_private_networks: bool = False  # SSRF protection; only for tests

    data_retention_days: int = 90


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
