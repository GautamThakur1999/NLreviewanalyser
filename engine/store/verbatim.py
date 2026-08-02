"""
T-P1-01 - Verbatim schema.

The central data contract every stage depends on. Deterministic IDs make
re-collection idempotent.

Guards: EC-N-10, EC-D-06
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from engine.normalise.text import (
    content_hash as _content_hash,
    hamming_distance,
    normalise_text,
    simhash as _simhash,
    verbatim_id as _verbatim_id,
)


# ---------------------------------------------------------------------------
# Verbatim — the immutable unit of analysis
# ---------------------------------------------------------------------------


class Verbatim(BaseModel):
    """
    The single data contract for every verbatim in the system.

    All fields are set at collection time and NEVER mutated afterwards.
    Later stages (gate, label, deduplicate) annotate by producing new
    documents, not by modifying this one.

    Field groups follow ARCH §4.1.
    """

    model_config = {"frozen": True}  # immutable after construction

    # ---- Identity -------------------------------------------------------
    verbatim_id: str = Field(
        ...,
        description="sha256(source + source_id)[:16] — stable across re-collections",
    )
    source: str = Field(..., description="'play_store' | 'app_store' | 'reddit' | ...")
    source_id: str = Field(..., description="Provider's native ID for this review/post")
    brand: str = Field(..., description="'blinkit' | 'zepto' | 'swiggy_instamart'")

    # ---- Provenance -----------------------------------------------------
    run_id: str = Field(..., description="The run_id that collected this verbatim")
    raw_payload_ref: str = Field(
        ...,
        description="'{run_id}/{source}_{brand}.jsonl.gz#L{n}' — resolves to the raw byte",
    )
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp when this record was written",
    )

    # ---- Content --------------------------------------------------------
    text_raw: str = Field(..., description="Original text, unmodified")
    text_clean: str = Field(
        ...,
        description="Output of normalise_text(text_raw) — the canonical form for all analysis",
    )
    content_hash: str = Field(..., description="SHA-256 of text_clean — for exact dedup")
    simhash: int = Field(..., description="64-bit SimHash of text_clean — for near-dedup")

    # ---- Attributes -----------------------------------------------------
    rating: int | None = Field(None, description="Star rating (1-5) or None if unavailable")
    rating_scale: int = Field(5, description="Maximum rating; always 5 for app stores")
    lang: str = Field("unknown", description="ISO 639-1 language code; 'hi' for Hinglish")
    lang_confidence: float = Field(0.0, ge=0.0, le=1.0)
    is_romanised: bool = Field(False, description="True if Indic language in Latin script")
    review_date: datetime | None = Field(None, description="When the review was written (UTC)")
    helpful_votes: int = Field(0, ge=0)
    duplicate_count: int = Field(
        1, ge=1, description="How many exact duplicates this represents (1 = no dups)"
    )

    # ---- Threading (Reddit / forums) ------------------------------------
    thread_id: str | None = None
    parent_id: str | None = None
    depth: int = Field(0, ge=0)

    # ---- Privacy --------------------------------------------------------
    author_hash: str | None = Field(
        None,
        description="HMAC-SHA256(author_id, PII_SALT)[:16]; None if author deleted/anonymous",
    )
    # replyContent is deliberately NOT a field — see T-P1-05, EC-C-17

    # ---- Engagement -----------------------------------------------------
    thumbs_up: int = Field(0, ge=0)
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific extras (e.g. video context for YouTube)",
    )

    # ---- Quarantine flag ------------------------------------------------
    quarantine_reason: str | None = Field(
        None,
        description="Set if this verbatim was quarantined; never None for processed verbatims",
    )

    # ---- Validators -----------------------------------------------------

    @field_validator("text_clean")
    @classmethod
    def text_clean_must_be_normalised(cls, v: str) -> str:
        """
        Assert text_clean is the output of normalise_text() (ST-02/03).

        This is an idempotency check: re-normalising text_clean must produce
        the same string. If it doesn't, the caller skipped normalise_text().
        """
        renormalised = normalise_text(v)
        if v != renormalised:
            raise ValueError(
                "text_clean is not the output of normalise_text(). "
                f"Expected: {renormalised[:80]!r}, got: {v[:80]!r}. "
                "Always call engine.normalise.text.normalise_text() before constructing Verbatim."
            )
        return v

    @field_validator("verbatim_id")
    @classmethod
    def verbatim_id_format(cls, v: str) -> str:
        if len(v) != 16 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError(
                f"verbatim_id must be a 16-char hex string, got: {v!r}. "
                "Use engine.normalise.text.verbatim_id(source, source_id)."
            )
        return v

    @field_validator("rating")
    @classmethod
    def rating_in_range(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError(f"rating must be 1-5, got {v}")
        return v


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def make_verbatim(
    *,
    source: str,
    source_id: str,
    brand: str,
    run_id: str,
    raw_payload_ref: str,
    text_raw: str,
    rating: int | None = None,
    rating_scale: int = 5,
    review_date: datetime | None = None,
    helpful_votes: int = 0,
    thumbs_up: int = 0,
    thread_id: str | None = None,
    parent_id: str | None = None,
    depth: int = 0,
    author_hash: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Verbatim:
    """
    Canonical factory for Verbatim. Handles normalisation and hash derivation.

    This is the only correct way to construct a Verbatim — do not construct
    directly except in tests that are explicitly testing field validation.
    """
    clean = normalise_text(text_raw)
    vid = _verbatim_id(source, source_id)
    ch = _content_hash(clean)
    sh = _simhash(clean)

    return Verbatim(
        verbatim_id=vid,
        source=source,
        source_id=source_id,
        brand=brand,
        run_id=run_id,
        raw_payload_ref=raw_payload_ref,
        text_raw=text_raw,
        text_clean=clean,
        content_hash=ch,
        simhash=sh,
        rating=rating,
        rating_scale=rating_scale,
        review_date=review_date,
        helpful_votes=helpful_votes,
        thumbs_up=thumbs_up,
        thread_id=thread_id,
        parent_id=parent_id,
        depth=depth,
        author_hash=author_hash,
        meta=meta or {},
    )


def assert_unique_ids(verbatims: list[Verbatim]) -> None:
    """
    Assert no two Verbatims share a verbatim_id. Call at write time (EC-D-06).
    """
    seen: set[str] = set()
    for v in verbatims:
        if v.verbatim_id in seen:
            raise ValueError(
                f"Duplicate verbatim_id detected: {v.verbatim_id}. "
                f"source={v.source} source_id={v.source_id}"
            )
        seen.add(v.verbatim_id)
