"""
T-P0-07 — Safety-block detection and reroute.

Wraps complete_structured() with a shared safety-block detector that:
1. Detects SAFETY_BLOCK finish reasons explicitly (not as "empty" or "irrelevant")
2. Reroutes blocked items to the other provider once
3. Counts blocks by (provider, language) into the manifest

This is an S1 bias mechanism: Indian review text contains profanity and heated
complaints. If a safety layer silently refuses these, the most diagnostic
feedback disappears while the pipeline reports success (EC-M-14).

Guards: EC-M-14, EC-V-08
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from engine.llm.base import (
    FinishReason,
    LLMClient,
    LLMSafetyBlockError,
    StructuredResult,
)
from engine.clean.pii import check_for_pii

logger = logging.getLogger(__name__)

class LLMPIIError(Exception):
    """Raised when outbound payload still contains unredacted PII."""
    pass


class SafetyBlockRecord:
    """Accumulates block counts by (provider, language) for the manifest."""

    def __init__(self) -> None:
        # key: (provider, language) → count
        self._counts: dict[tuple[str, str], int] = defaultdict(int)

    def record(self, provider: str, language: str = "unknown") -> None:
        self._counts[(provider, language)] += 1
        logger.warning(
            "Safety block recorded: provider=%s language=%s total=%d",
            provider,
            language,
            self._counts[(provider, language)],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            f"{provider}:{lang}": count
            for (provider, lang), count in self._counts.items()
        }

    @property
    def total(self) -> int:
        return sum(self._counts.values())


# Global block registry (flushed into the manifest by the manifest writer)
safety_block_registry = SafetyBlockRecord()


def call_with_safety_reroute(
    primary: LLMClient,
    fallback: LLMClient,
    system: str,
    user: str,
    schema: type[BaseModel],
    cache_handle: str | None = None,
    language: str = "unknown",
) -> StructuredResult:
    """
    Call primary provider; on SAFETY_BLOCK, reroute to fallback once.

    On block by both providers, the item is recorded as blocked-and-rerouted —
    it is NEVER silently absent from the manifest (EC-M-14).

    Args:
        primary:      The preferred LLMClient for this verbatim.
        fallback:     The alternative provider to try on block.
        system/user:  Prompt content (built by build_prompt()).
        schema:       Pydantic schema to parse into.
        cache_handle: Optional context-cache handle (passed to primary only).
        language:     Detected language of the verbatim (for block counting).

    Returns:
        StructuredResult from whichever provider succeeded.

    Raises:
        LLMSafetyBlockError if both providers refused the item.
        LLMPIIError if the outbound payload contains unredacted PII.
    """
    if check_for_pii(user) or check_for_pii(system):
        raise LLMPIIError("Outbound payload contains unredacted PII (EC-P-07). Request aborted.")

    try:
        result = primary.complete_structured(
            system=system,
            user=user,
            schema=schema,
            cache_handle=cache_handle,
        )
        return result
    except LLMSafetyBlockError as primary_exc:
        safety_block_registry.record(primary.provider, language)
        logger.warning(
            "Primary provider %s blocked item (lang=%s). Rerouting to %s.",
            primary.provider,
            language,
            fallback.provider,
        )

        # Reroute to fallback — once only, no recursion
        try:
            result = fallback.complete_structured(
                system=system,
                user=user,
                schema=schema,
                cache_handle=None,  # cache handles are provider-specific
            )
            logger.info(
                "Fallback provider %s labelled item blocked by %s.",
                fallback.provider,
                primary.provider,
            )
            return result
        except LLMSafetyBlockError as fallback_exc:
            safety_block_registry.record(fallback.provider, language)
            logger.error(
                "Both providers blocked item (lang=%s). "
                "Item will be recorded as blocked-and-rerouted, not silently dropped.",
                language,
            )
            raise LLMSafetyBlockError(
                f"Both {primary.provider} and {fallback.provider} blocked this item. "
                f"Primary: {primary_exc}. Fallback: {fallback_exc}."
            ) from fallback_exc
