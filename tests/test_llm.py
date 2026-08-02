"""
Tests for T-P0-04 — LLM base types.
Tests for T-P0-07 — Safety-block reroute.
Tests for T-P0-10 — Cost accounting.

Uses unittest.mock to avoid any real LLM calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from engine.llm.base import (
    BudgetExceeded,
    FinishReason,
    LLMSafetyBlockError,
    StructuredResult,
    TokenUsage,
)
from engine.llm.router import SafetyBlockRecord, call_with_safety_reroute
from engine.store.cost import CostAccumulator


# ─────────────────────────────────────────────────────────────────────────────
# FinishReason
# ─────────────────────────────────────────────────────────────────────────────


class TestFinishReason:
    def test_safety_block_is_distinct(self):
        """SAFETY_BLOCK must never equal EMPTY or COMPLETE."""
        assert FinishReason.SAFETY_BLOCK != FinishReason.EMPTY
        assert FinishReason.SAFETY_BLOCK != FinishReason.COMPLETE
        assert FinishReason.SAFETY_BLOCK != FinishReason.TRUNCATED

    def test_all_values_distinct(self):
        values = list(FinishReason)
        assert len(values) == len(set(values))


# ─────────────────────────────────────────────────────────────────────────────
# TokenUsage
# ─────────────────────────────────────────────────────────────────────────────


class TestTokenUsage:
    def test_total_tokens(self):
        u = TokenUsage(prompt_tokens=100, completion_tokens=50, cached_tokens=20)
        assert u.total_tokens == 150  # prompt + completion (cached is part of prompt)

    def test_addition(self):
        u1 = TokenUsage(prompt_tokens=100, completion_tokens=50, cached_tokens=10)
        u2 = TokenUsage(prompt_tokens=200, completion_tokens=100, cached_tokens=30)
        u3 = u1 + u2
        assert u3.prompt_tokens == 300
        assert u3.completion_tokens == 150
        assert u3.cached_tokens == 40


# ─────────────────────────────────────────────────────────────────────────────
# Safety-block reroute (T-P0-07)
# ─────────────────────────────────────────────────────────────────────────────


class TestSafetyReroute:
    def _make_mock_client(self, provider: str, model: str, result=None, raises=None):
        client = MagicMock()
        client.provider = provider
        client.model = model
        if raises:
            client.complete_structured.side_effect = raises
        elif result is not None:
            client.complete_structured.return_value = result
        return client

    def test_primary_success_no_reroute(self):
        """Primary succeeds — fallback never called."""
        from pydantic import BaseModel

        class DummySchema(BaseModel):
            value: str

        expected = StructuredResult(
            parsed=DummySchema(value="ok"),
            finish_reason=FinishReason.COMPLETE,
        )
        primary = self._make_mock_client("groq", "fast-model", result=expected)
        fallback = self._make_mock_client("gemini", "flash-model")

        result = call_with_safety_reroute(
            primary, fallback, "system", "user", DummySchema
        )
        assert result.finish_reason == FinishReason.COMPLETE
        fallback.complete_structured.assert_not_called()

    def test_primary_blocked_reroutes_to_fallback(self):
        from pydantic import BaseModel

        class DummySchema(BaseModel):
            value: str

        fallback_result = StructuredResult(
            parsed=DummySchema(value="ok_from_fallback"),
            finish_reason=FinishReason.COMPLETE,
        )
        primary = self._make_mock_client(
            "groq", "fast-model", raises=LLMSafetyBlockError("blocked")
        )
        fallback = self._make_mock_client("gemini", "flash-model", result=fallback_result)

        result = call_with_safety_reroute(
            primary, fallback, "system", "user", DummySchema
        )
        assert result.parsed.value == "ok_from_fallback"
        fallback.complete_structured.assert_called_once()

    def test_both_blocked_raises(self):
        from pydantic import BaseModel

        class DummySchema(BaseModel):
            value: str

        primary = self._make_mock_client(
            "groq", "fast-model", raises=LLMSafetyBlockError("blocked")
        )
        fallback = self._make_mock_client(
            "gemini", "flash-model", raises=LLMSafetyBlockError("also blocked")
        )

        with pytest.raises(LLMSafetyBlockError):
            call_with_safety_reroute(
                primary, fallback, "system", "user", DummySchema
            )

    def test_block_counter_increments(self):
        from pydantic import BaseModel

        class DummySchema(BaseModel):
            value: str

        registry = SafetyBlockRecord()
        registry.record("groq", "en")
        registry.record("groq", "hi")
        registry.record("gemini", "en")

        assert registry.total == 3
        d = registry.to_dict()
        assert "groq:en" in d
        assert d["groq:en"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Cost accounting (T-P0-10)
# ─────────────────────────────────────────────────────────────────────────────


class TestCostAccumulator:
    def test_no_breach_under_ceiling(self):
        acc = CostAccumulator(ceiling_usd=10.0)
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        acc.record("groq", usage)
        acc.check_ceiling()  # should not raise

    def test_breach_raises_budget_exceeded(self):
        acc = CostAccumulator(ceiling_usd=0.001)
        usage = TokenUsage(prompt_tokens=1_000_000, completion_tokens=500_000)
        acc.record("gemini", usage)
        with pytest.raises(BudgetExceeded):
            acc.check_ceiling()

    def test_cost_accumulates(self):
        acc = CostAccumulator(ceiling_usd=100.0)
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        cost1 = acc.record("groq", usage)
        cost2 = acc.record("groq", usage)
        assert abs(acc.total_cost_usd - (cost1 + cost2)) < 1e-9

    def test_gemini_cached_tokens_cheaper(self):
        acc = CostAccumulator()
        # Same prompt tokens but all cached
        uncached = TokenUsage(prompt_tokens=1000, completion_tokens=100, cached_tokens=0)
        cached = TokenUsage(prompt_tokens=1000, completion_tokens=100, cached_tokens=1000)
        cost_uncached = acc.estimate_cost("gemini", uncached)
        cost_cached = acc.estimate_cost("gemini", cached)
        assert cost_cached < cost_uncached  # caching reduces cost
