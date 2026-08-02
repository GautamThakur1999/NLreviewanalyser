from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class GroundednessResult(BaseModel):
    pass_rate: float = Field(..., description="Percentage of quotes that exact-matched to the source verbatim.")
    total_quotes_checked: int
    whitespace_normalised_passes: int
    failed_quotes: List[str] = Field(default_factory=list)

class CoverageResult(BaseModel):
    processed_verbatims_count: int
    mapped_verbatims_count: int
    coverage_percentage: float = Field(..., description="% of processed relevant verbatims mapping to >=1 theme")
    gate_exclusion_rate: float
    gate_exclusion_reasons: Dict[str, int] = Field(default_factory=dict)

class TriangulationResult(BaseModel):
    theme_source_matrix: Dict[str, Dict[str, int]] = Field(..., description="Theme ID -> Source -> Count")
    downgraded_themes: List[str] = Field(default_factory=list, description="Themes downgraded in confidence due to being single-source")

class BiasReport(BaseModel):
    skews: Dict[str, Dict[str, str]] = Field(..., description="Skew name -> {'magnitude': str, 'direction': str}")

class QuotaSamplingBias(BaseModel):
    stratum_fractions: Dict[str, float]
    unprocessed_share_by_source: Dict[str, float]
    truncation_rate: float
    bias_directions: Dict[str, str]

class ReliabilityResult(BaseModel):
    cohens_kappa: Dict[str, float] = Field(..., description="Dimension -> Kappa value")
    per_class_prevalence: Dict[str, float]
    unreliable_classes: List[str] = Field(default_factory=list)

class ValidationHarnessOutput(BaseModel):
    run_id: str
    snapshot_id: str
    groundedness: GroundednessResult
    coverage: CoverageResult
    triangulation: TriangulationResult
    bias: BiasReport
    quota_sampling: QuotaSamplingBias
    reliability: Optional[ReliabilityResult] = None
    stability_overlap_score: Optional[float] = None
    cross_provider_kappa: Optional[Dict[str, float]] = None
