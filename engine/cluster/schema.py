"""
Theme schema - Phase 5
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

class ThemeEvidence(BaseModel):
    verbatim_id: str
    quote: str
    start: int | None
    end: int | None
    is_grounded: bool

class ThemeDistribution(BaseModel):
    source_counts: dict[str, int] = Field(default_factory=dict)
    brand_counts: dict[str, int] = Field(default_factory=dict)
    brand_attribution: dict[str, float] = Field(default_factory=dict)

class Theme(BaseModel):
    theme_id: str
    name: str
    barrier_type: BarrierType
    mention_count: int = 0
    first_seen_at_doc_n: int = -1
    evidence: list[ThemeEvidence] = Field(default_factory=list)
    distribution: ThemeDistribution = Field(default_factory=ThemeDistribution)

class ThemeCollection(BaseModel):
    themes: list[Theme] = Field(default_factory=list)
