"""
T-P0-10 — Cost accounting and hard budget ceiling.

Per-call token/cost capture flowing into the manifest. A configured ceiling
that aborts at a resumable checkpoint before any spend is irreversible.

Re-runs (stability check, codebook revision, cross-provider validation) are
validation *requirements* — a one-pass-only budget cannot be validated (ARCH §16.3).

Guards: EC-M-25
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from engine.llm.base import BudgetExceeded, TokenUsage

logger = logging.getLogger(__name__)


@dataclass
class CostAccumulator:
    """
    Tracks running cost and token usage across all LLM calls in a run.

    Updated from every StructuredResult.usage. Checks against the ceiling
    before each chunk submission (EC-M-25).
    """

    # Provider pricing (fill from T-P0-11 spike and T-P0-13 live rates)
    # Defaults are ESTIMATES — update after the spike run.
    groq_input_per_1m_tokens: float = 0.05      # USD (estimated free-tier cost basis)
    groq_output_per_1m_tokens: float = 0.08
    gemini_input_per_1m_tokens: float = 0.075    # Flash tier estimate
    gemini_output_per_1m_tokens: float = 0.30
    gemini_cache_per_1m_tokens: float = 0.01875  # Cached read discount

    ceiling_usd: float = 5.0
    warn_at_fraction: float = 0.8

    total_cost_usd: float = field(default=0.0, init=False)
    total_usage: TokenUsage = field(default_factory=TokenUsage, init=False)
    _warned: bool = field(default=False, init=False)

    def estimate_cost(self, provider: str, usage: TokenUsage) -> float:
        """Estimate USD cost for one call given provider and token usage."""
        if provider == "groq":
            input_rate = self.groq_input_per_1m_tokens
            output_rate = self.groq_output_per_1m_tokens
            cache_rate = 0.0
        else:  # gemini
            input_rate = self.gemini_input_per_1m_tokens
            output_rate = self.gemini_output_per_1m_tokens
            cache_rate = self.gemini_cache_per_1m_tokens

        non_cached_prompt = max(0, usage.prompt_tokens - usage.cached_tokens)
        cost = (
            (non_cached_prompt / 1_000_000) * input_rate
            + (usage.cached_tokens / 1_000_000) * cache_rate
            + (usage.completion_tokens / 1_000_000) * output_rate
        )
        return cost

    def record(self, provider: str, usage: TokenUsage) -> float:
        """
        Accumulate cost from one call. Returns the cost of this call.
        Does NOT check the ceiling — call check_ceiling() before each chunk.
        """
        cost = self.estimate_cost(provider, usage)
        self.total_cost_usd += cost
        self.total_usage = self.total_usage + usage

        # Warn at 80% (or configured fraction)
        if (
            not self._warned
            and self.total_cost_usd >= self.ceiling_usd * self.warn_at_fraction
        ):
            logger.warning(
                "Budget warning: %.2f USD spent of %.2f USD ceiling (%.0f%%).",
                self.total_cost_usd,
                self.ceiling_usd,
                100 * self.total_cost_usd / self.ceiling_usd,
            )
            self._warned = True

        return cost

    def check_ceiling(self) -> None:
        """
        Raise BudgetExceeded if the ceiling has been hit.

        The runner catches this to checkpoint state and exit cleanly — it is NOT
        a crash. State must be saved before this is called (ST-10).
        """
        if self.total_cost_usd >= self.ceiling_usd:
            raise BudgetExceeded(
                f"Hard budget ceiling reached: {self.total_cost_usd:.4f} USD "
                f"≥ {self.ceiling_usd:.2f} USD ceiling. "
                "Run is checkpointed. Resume with the same run_id. "
                "Increase cost.ceiling_usd in settings.yaml to continue further."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cost_usd": round(self.total_cost_usd, 6),
            "ceiling_usd": self.ceiling_usd,
            "prompt_tokens": self.total_usage.prompt_tokens,
            "completion_tokens": self.total_usage.completion_tokens,
            "cached_tokens": self.total_usage.cached_tokens,
            "total_tokens": self.total_usage.total_tokens,
            "rates_are_estimates": True,  # Updated after T-P0-11 spike
        }
