"""
T-P0-14 — Token budget planner (pre-flight).

Computes full-pass feasibility from MEASURED (not estimated) figures from the
T-P0-11 spike. If infeasible under daily quota, computes the largest stratified
sample that fits.

The stability re-run and cross-provider check are budgeted as requirements (not
extras) — a design that can only afford one pass cannot be validated (ARCH §16.3).

Phase 4 refuses to start without explicit plan approval (flag in manifest).

Guards: EC-B-09, EC-B-10, EC-M-25
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProviderLimits:
    """Quota limits for one provider/model slot (from T-P0-13)."""

    provider: str
    model: str
    tpd: int | None = None       # Tokens per day — the binding free-tier constraint
    tpm: int | None = None
    rpm: int | None = None
    rpd: int | None = None


@dataclass
class SpikeMeasurement:
    """Measured values from T-P0-11 (filled in after the spike run)."""

    avg_prompt_tokens_per_doc: float = 0.0
    avg_completion_tokens_per_doc: float = 0.0
    avg_cached_tokens_per_doc: float = 0.0

    @property
    def net_tokens_per_doc(self) -> float:
        """Billable tokens per document (non-cached prompt + completion)."""
        non_cached = max(0, self.avg_prompt_tokens_per_doc - self.avg_cached_tokens_per_doc)
        return non_cached + self.avg_completion_tokens_per_doc


@dataclass
class BudgetPlan:
    """Output of the planner — archived to manifest; Phase 4 needs approval flag."""

    full_corpus_size: int
    relevant_subset_size: int

    gate_days: float = 0.0
    label_days: float = 0.0
    stability_rerun_days: float = 0.0
    cross_provider_days: float = 0.0
    total_days: float = 0.0

    full_pass_feasible: bool = False
    affordable_sample_size: int | None = None

    projected_cost_usd: float = 0.0
    budget_ceiling_usd: float = 0.0

    wall_clock_window_days: int = 7
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_corpus_size": self.full_corpus_size,
            "relevant_subset_size": self.relevant_subset_size,
            "gate_days": round(self.gate_days, 2),
            "label_days": round(self.label_days, 2),
            "stability_rerun_days": round(self.stability_rerun_days, 2),
            "cross_provider_days": round(self.cross_provider_days, 2),
            "total_days": round(self.total_days, 2),
            "full_pass_feasible": self.full_pass_feasible,
            "affordable_sample_size": self.affordable_sample_size,
            "projected_cost_usd": round(self.projected_cost_usd, 4),
            "budget_ceiling_usd": self.budget_ceiling_usd,
            "wall_clock_window_days": self.wall_clock_window_days,
            "notes": self.notes,
        }

    def summary(self) -> str:
        lines = [
            "═══ TOKEN BUDGET PLAN ═══",
            f"  Corpus:              {self.full_corpus_size:,} docs",
            f"  Relevant subset:     {self.relevant_subset_size:,} docs (estimated)",
            f"  Gate pass:           {self.gate_days:.1f} day(s)",
            f"  Label pass:          {self.label_days:.1f} day(s)",
            f"  Stability re-run:    {self.stability_rerun_days:.1f} day(s)",
            f"  Cross-provider:      {self.cross_provider_days:.1f} day(s)",
            f"  ─────────────────────",
            f"  Total:               {self.total_days:.1f} day(s) "
            f"(window: {self.wall_clock_window_days}d)",
            f"  Feasible:            {'✓ YES' if self.full_pass_feasible else '✗ NO'}",
        ]
        if not self.full_pass_feasible and self.affordable_sample_size:
            lines.append(
                f"  Affordable sample:   {self.affordable_sample_size:,} docs "
                "(stratified, seeds recorded)"
            )
        lines += [
            f"  Projected cost:      ${self.projected_cost_usd:.4f} USD "
            f"(ceiling: ${self.budget_ceiling_usd:.2f})",
        ]
        for note in self.notes:
            lines.append(f"  NOTE: {note}")
        lines.append("═══ END PLAN ═══")
        return "\n".join(lines)


def compute_budget_plan(
    gate_limits: ProviderLimits,
    label_limits: ProviderLimits,
    gate_spike: SpikeMeasurement,
    label_spike: SpikeMeasurement,
    corpus_size: int,
    gate_pass_rate: float = 0.6,       # estimated fraction passing the gate
    wall_clock_window_days: int = 7,
    cost_ceiling_usd: float = 5.0,
    groq_input_rate: float = 0.05,     # USD per 1M tokens — update from spike
    gemini_input_rate: float = 0.075,
    gemini_output_rate: float = 0.30,
) -> BudgetPlan:
    """
    Compute feasibility under free-tier daily quota.

    Measurements from T-P0-11 spike MUST be used, not estimates.
    (That's why the function requires SpikeMeasurement, not just corpus_size.)
    """
    relevant_size = int(corpus_size * gate_pass_rate)
    cross_provider_sample = min(200, relevant_size)  # §12.8

    plan = BudgetPlan(
        full_corpus_size=corpus_size,
        relevant_subset_size=relevant_size,
        budget_ceiling_usd=cost_ceiling_usd,
        wall_clock_window_days=wall_clock_window_days,
    )

    if gate_spike.net_tokens_per_doc <= 0 or label_spike.net_tokens_per_doc <= 0:
        plan.notes.append(
            "Spike measurements are zero — run T-P0-11 first and fill in "
            "SpikeMeasurement before using the budget planner."
        )
        return plan

    # Gate (Groq)
    gate_tokens_total = corpus_size * gate_spike.net_tokens_per_doc
    gate_tpd = gate_limits.tpd or 1  # avoid div-by-zero
    plan.gate_days = gate_tokens_total / gate_tpd

    # Label (Gemini)
    label_tokens_total = relevant_size * label_spike.net_tokens_per_doc
    label_tpd = label_limits.tpd or 1
    plan.label_days = label_tokens_total / label_tpd

    # Stability re-run (1× label pass — mandatory, ARCH §16.3)
    plan.stability_rerun_days = plan.label_days

    # Cross-provider check (~200 docs on both providers)
    cross_gate_tokens = cross_provider_sample * gate_spike.net_tokens_per_doc
    cross_label_tokens = cross_provider_sample * label_spike.net_tokens_per_doc
    cross_gate_days = cross_gate_tokens / gate_tpd
    cross_label_days = cross_label_tokens / label_tpd
    plan.cross_provider_days = cross_gate_days + cross_label_days

    plan.total_days = (
        plan.gate_days
        + plan.label_days
        + plan.stability_rerun_days
        + plan.cross_provider_days
    )

    plan.full_pass_feasible = plan.total_days <= wall_clock_window_days

    if not plan.full_pass_feasible:
        # Compute largest affordable sample
        label_budget_days = wall_clock_window_days - plan.gate_days - plan.cross_provider_days
        # Reserve half for stability re-run
        single_pass_days = max(0.0, label_budget_days / 2)
        affordable_docs = int(single_pass_days * label_tpd / label_spike.net_tokens_per_doc)
        plan.affordable_sample_size = min(affordable_docs, relevant_size)
        plan.notes.append(
            f"Full pass infeasible in {wall_clock_window_days}d window. "
            f"Use stratified sample of {plan.affordable_sample_size:,} docs "
            "(stratify by source × brand × language × rating × time period). "
            "Document as a corpus limitation in bias section (ARCH §12.7)."
        )

    # Rough cost estimate
    gate_cost = (gate_tokens_total / 1_000_000) * groq_input_rate
    label_input_cost = (label_tokens_total / 1_000_000) * gemini_input_rate
    label_output_cost = (
        relevant_size * label_spike.avg_completion_tokens_per_doc / 1_000_000
    ) * gemini_output_rate
    plan.projected_cost_usd = gate_cost + label_input_cost + label_output_cost

    if plan.projected_cost_usd > cost_ceiling_usd:
        plan.notes.append(
            f"Projected cost ${plan.projected_cost_usd:.4f} exceeds ceiling "
            f"${cost_ceiling_usd:.2f}. Reduce sample size or increase ceiling."
        )

    return plan
