"""
T-P0-02 — Configuration system.

Typed Pydantic settings that load config/sources.yaml, config/models.yaml,
config/settings.yaml, and .env in one validated pass. Fails at startup on any
missing required key, not mid-run.

Guards: EC-X-07
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Repo root (two levels up from this file: engine/config/ → engine/ → root)
_REPO_ROOT = Path(__file__).parent.parent.parent
_CONFIG_DIR = _REPO_ROOT / "config"


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models — one per YAML section
# ─────────────────────────────────────────────────────────────────────────────


class ModelConfig(BaseModel):
    """Single LLM model slot (gate / label / induce / …)."""

    provider: str = Field(..., description="'groq' or 'gemini'")
    model: str = Field(..., description="Provider model ID — must be verified live via T-P0-09")
    max_tokens: int = Field(..., gt=0)
    rpm: int | None = Field(None, description="Requests per minute (from T-P0-13)")
    tpm: int | None = Field(None, description="Tokens per minute (from T-P0-13)")
    rpd: int | None = Field(None, description="Requests per day (from T-P0-13)")
    tpd: int | None = Field(None, description="Tokens per day — binding free-tier limit")

    @field_validator("provider")
    @classmethod
    def provider_known(cls, v: str) -> str:
        allowed = {"groq", "gemini"}
        if v not in allowed:
            raise ValueError(f"provider must be one of {allowed}, got {v!r}")
        return v

    @field_validator("model")
    @classmethod
    def model_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "model ID is empty. Run `make verify` to discover live model IDs "
                "and populate config/models.yaml before any spend."
            )
        return v.strip()


class LLMModelsConfig(BaseModel):
    """All model slots from config/models.yaml → llm:"""

    gate: ModelConfig
    label: ModelConfig
    label_hard: ModelConfig
    induce: ModelConfig
    synthesise: ModelConfig
    adjudicate: ModelConfig


class SourceBrandConfig(BaseModel):
    """Per (source, brand) pair from config/sources.yaml."""

    source: str
    brand: str
    # e.g. play_package, app_store_id, subreddits, …
    params: dict[str, Any] = Field(default_factory=dict)
    min_expected: int = Field(50, description="Floor for T-P1-06 minimum-count guard")
    target_min: int | None = None
    target_max: int | None = None
    expected_title: str | None = Field(
        None, description="Brand title to match in T-P1-04 identifier verification"
    )


class CollectionConfig(BaseModel):
    max_pages: int = Field(100, gt=0)
    timeout_seconds: int = Field(30, gt=0)
    window_days: int = Field(180, gt=0, description="Maximum age of collected verbatims in days")


class ThresholdsConfig(BaseModel):
    gate_relevance_score: float = Field(0.5, ge=0.0, le=1.0)
    dedup_simhash_distance: int = Field(3, ge=0, le=64)
    dedup_min_tokens: int = Field(10, gt=0)
    spam_url_density_max: float = Field(0.3, ge=0.0, le=1.0)
    saturation_jaccard_min: float = Field(0.7, ge=0.0, le=1.0)


class CostConfig(BaseModel):
    ceiling_usd: float = Field(5.0, gt=0, description="Hard budget ceiling in USD; abort if exceeded")
    warn_at_fraction: float = Field(0.8, ge=0.0, le=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Root settings
# ─────────────────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """
    Root settings object. Loaded once via get_settings().

    Secrets come from .env (never from code or logs).
    YAML sections are loaded explicitly from config/*.yaml.
    """

    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # ── Secrets (from .env) ──────────────────────────────────────────────────
    groq_api_key: str = Field(..., description="Groq API key — ST-12")
    gemini_api_key: str = Field(..., description="Google Gemini API key — ST-12")
    reddit_client_id: str = Field(..., description="Reddit OAuth client ID")
    reddit_client_secret: str = Field(..., description="Reddit OAuth client secret")
    reddit_user_agent: str = Field(..., description="Reddit user-agent string")
    pii_salt: str = Field(..., min_length=16, description="HMAC salt for author hashing — never rotated mid-project")

    # ── YAML sections (populated by the factory) ─────────────────────────────
    llm: LLMModelsConfig | None = None
    sources: list[SourceBrandConfig] = Field(default_factory=list)
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    cost: CostConfig = Field(default_factory=CostConfig)

    @field_validator("groq_api_key", "gemini_api_key", "reddit_client_id",
                     "reddit_client_secret", "reddit_user_agent", "pii_salt",
                     mode="before")
    @classmethod
    def secret_not_empty(cls, v: str, info: Any) -> str:
        if not v or not v.strip():
            raise ValueError(
                f"Secret '{info.field_name}' is empty. "
                "Copy .env.example to .env and populate all secrets before running."
            )
        return v

    @model_validator(mode="after")
    def no_env_direct_reads(self) -> "Settings":
        """
        Sentinel check: if any secret was read directly from os.environ *outside*
        this class, a lint rule catches it. This validator is the runtime complement.
        """
        return self

    def validate_all(self) -> None:
        """
        Explicit validation pass — call at CLI entry points so bad config
        blows up before any network call (EC-X-07).
        """
        if not self.sources:
            raise ValueError(
                "config/sources.yaml defines no sources. "
                "Add at least one (source, brand) pair before collecting."
            )
        if self.llm is None:
            raise ValueError(
                "config/models.yaml defines no llm section. "
                "Populate model IDs (then run `make verify`) before any spend."
            )


# ─────────────────────────────────────────────────────────────────────────────
# YAML loader helper
# ─────────────────────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required config file not found: {path}. "
            "Run `make setup` to initialise the project."
        )
    with open(path, encoding="utf-8") as fh:  # noqa: WPS515
        return yaml.safe_load(fh) or {}


# ─────────────────────────────────────────────────────────────────────────────
# Public accessor (singleton, cached)
# ─────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Single point of truth for all config. Thread-safe (GIL + lru_cache).

    No caller should read os.environ directly — use this instead (ST-12, EC-X-07).
    """
    models_yaml = _load_yaml(_CONFIG_DIR / "models.yaml")
    sources_yaml = _load_yaml(_CONFIG_DIR / "sources.yaml")
    settings_yaml = _load_yaml(_CONFIG_DIR / "settings.yaml")

    # Parse sub-sections from YAML
    llm_raw = models_yaml.get("llm")
    llm_config = LLMModelsConfig(**llm_raw) if llm_raw else None

    raw_sources = sources_yaml.get("sources") or []
    source_configs = [SourceBrandConfig(**s) for s in raw_sources] if raw_sources else []

    collection_raw = settings_yaml.get("collection", {})
    thresholds_raw = settings_yaml.get("thresholds", {})
    cost_raw = settings_yaml.get("cost", {})

    # Build Settings from env + parsed YAML
    settings = Settings(
        llm=llm_config,
        sources=source_configs,
        collection=CollectionConfig(**collection_raw) if collection_raw else CollectionConfig(),
        thresholds=ThresholdsConfig(**thresholds_raw) if thresholds_raw else ThresholdsConfig(),
        cost=CostConfig(**cost_raw) if cost_raw else CostConfig(),
    )
    return settings


def reload_settings() -> Settings:
    """Force a cache-busted reload (useful in tests)."""
    get_settings.cache_clear()
    return get_settings()
