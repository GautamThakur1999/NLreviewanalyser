"""
T-P4-01 - Label schema

Defines the core Pydantic model for Phase 4 labelling.
Enforces strict enum validation for barrier_types and sentiment.
Includes EvidenceSpan with recomputed start/end offsets.
"""

from typing import Literal
from pydantic import BaseModel, Field

BarrierType = Literal[
    "app_ux_and_support",
    "pricing_and_fees",
    "not_a_barrier",
    "delivery_and_logistics",
    "product_availability",
    "trust_and_safety",
    "quality_and_freshness"
]

Sentiment = Literal["positive", "neutral", "negative"]


class EvidenceSpan(BaseModel):
    """
    A single evidence span attributing a label to a verbatim text.
    The LLM provides the `quote`. The matcher recomputes `start` and `end`.
    """
    quote: str = Field(..., description="The exact verbatim substring that justifies this label.")
    start: int | None = Field(None, description="Recomputed 0-indexed start character offset in text_clean.")
    end: int | None = Field(None, description="Recomputed 0-indexed end character offset in text_clean.")
    is_grounded: bool = Field(False, description="True if the quote was successfully exact-matched in the text.")


class AssignedCode(BaseModel):
    code_name: str = Field(..., description="The specific code name from the codebook (e.g., 'high_prices').")
    barrier_type: BarrierType = Field(..., description="The high-level category this code belongs to.")
    evidence: list[EvidenceSpan] = Field(..., description="Exact quotes justifying this specific code.")


class Label(BaseModel):
    verbatim_id: str = Field(..., description="The ID of the verbatim being labelled.")
    is_relevant: bool = Field(..., description="True if the review describes an exploration barrier/driver.")
    sentiment: Sentiment = Field(..., description="Overall sentiment of the review.")
    assigned_codes: list[AssignedCode] = Field(
        default_factory=list,
        description="List of specific codes applied to this review."
    )
    provider: str | None = Field(None, description="The LLM provider used (e.g., 'groq').")
    model: str | None = Field(None, description="The specific model used.")
    codebook_version: str | None = Field(None, description="Codebook version used (e.g., 'v1').")
    truncated: bool = Field(False, description="True if the document was truncated before labelling.")

    # ARCH §4.2 fields
    run_id: str | None = Field(None, description="Unique run execution identifier.")


class BatchLabel(BaseModel):
    """Wrapper for LLM output."""
    labels: list[Label] = Field(..., description="The labels generated for the batch.")
