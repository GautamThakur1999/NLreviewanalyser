"""
Insight schema - Phase 5
"""
from typing import Literal
from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low"]

class Insight(BaseModel):
    insight_id: str
    research_question_id: str
    claim: str = Field(..., description="The core finding answering the research question.")
    mechanism: str = Field(..., description="The 'why' or 'how' behind the claim.")
    segment: str = Field(..., description="Who this primarily affects.")
    implication: str = Field(..., description="The business/product impact of this insight.")
    confidence: Confidence = Field(..., description="Computed confidence in this insight.")
    supporting_theme_ids: list[str] = Field(default_factory=list)
    contradicting_evidence: str | None = Field(None, description="Any evidence that points the other way, or explicitly null if none.")

class InsightCollection(BaseModel):
    insights: list[Insight] = Field(default_factory=list)
