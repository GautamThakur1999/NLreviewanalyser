"""
T-P0-04 — LLMClient protocol and shared types.

The vendor boundary (ARCH P8). No vendor SDK is imported here; this module
defines only the interfaces and data types. Implementations live in
groq_client.py and gemini_client.py.

Guards: EC-M-16; ST-08
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterator, Protocol, runtime_checkable

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# FinishReason — must distinguish safety blocks explicitly (EC-M-14)
# ─────────────────────────────────────────────────────────────────────────────


class FinishReason(str, Enum):
    """
    Why the model stopped generating.

    SAFETY_BLOCK is a distinct value — it must never be mapped to EMPTY or
    IRRELEVANT, because those mean different things and losing the distinction
    silently removes the most diagnostic feedback (EC-M-14).
    """

    COMPLETE = "complete"          # Normal, full response
    TRUNCATED = "truncated"        # Hit max_tokens; response is partial
    SAFETY_BLOCK = "safety_block"  # Provider content policy refusal
    EMPTY = "empty"                # Model returned nothing (not a block)
    ERROR = "error"                # Unclassified failure


# ─────────────────────────────────────────────────────────────────────────────
# Usage — token accounting for cost model and quota ledger
# ─────────────────────────────────────────────────────────────────────────────


class TokenUsage(BaseModel):
    """Token counts from a single LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = Field(
        0,
        description=(
            "Tokens served from a context cache (Gemini). "
            "Must be non-zero after the first batch when caching is configured; "
            "the pipeline asserts this (ARCH §9.5)."
        ),
    )

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
        )


# ─────────────────────────────────────────────────────────────────────────────
# StructuredResult — what every complete_structured() call returns
# ─────────────────────────────────────────────────────────────────────────────


class StructuredResult(BaseModel):
    """
    The uniform return type from LLMClient.complete_structured().

    .parsed  — a validated Pydantic model instance (the caller's schema)
    .usage   — token counts including cached tokens
    .finish_reason — FinishReason (never coerced; safety blocks are explicit)
    .raw     — the raw JSON string from the provider (for debugging)
    """

    parsed: Any = Field(description="Validated Pydantic model instance")
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: FinishReason = FinishReason.COMPLETE
    raw: str = Field("", description="Raw JSON response string — never logged in production")
    provider: str = ""
    model: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Batch types — request-ID keyed (ARCH §9.8 rule 1)
# ─────────────────────────────────────────────────────────────────────────────


class BatchRequest(BaseModel):
    """
    A single entry in a batch submission.

    request_id is mandatory and caller-assigned — results MUST be matched by
    this ID, never by position (ARCH §9.8).
    """

    request_id: str = Field(..., description="Caller-assigned; results keyed on this")
    system: str
    user: str
    schema_name: str = Field(
        ..., description="Fully-qualified name of the Pydantic schema class"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class BatchHandle(BaseModel):
    """Opaque reference to a submitted batch."""

    provider: str
    handle_id: str
    submitted_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchResult(BaseModel):
    """
    Result for one item in a batch. Matched by request_id.

    If finish_reason is SAFETY_BLOCK, parsed will be None.
    """

    request_id: str
    result: StructuredResult | None = None
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# LLMClient Protocol — the only interface the rest of the pipeline may use
# ─────────────────────────────────────────────────────────────────────────────


@runtime_checkable
class LLMClient(Protocol):
    """
    The single interface every LLM caller uses. No vendor SDK outside engine/llm/.

    Implementations: GroqClient, GeminiClient.
    Model IDs come from config, never from code (ARCH §9.6).
    """

    provider: str
    model: str

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[BaseModel],
        cache_handle: str | None = None,
    ) -> StructuredResult:
        """
        Make a single synchronous structured call.

        Args:
            system:       System-prompt text (built by build_prompt()).
            user:         User-turn text (built by build_prompt()).
            schema:       The Pydantic model class to parse into.
            cache_handle: Opaque context-cache handle (Gemini only; ignored by Groq).

        Returns:
            StructuredResult with a validated .parsed instance.

        Raises:
            LLMValidationError if the response cannot be parsed (retryable).
            LLMRateLimitError  if the provider returns 429 after all retries.
            LLMError           for all other failures.
        """
        ...

    def submit_batch(self, requests: list[BatchRequest]) -> BatchHandle:
        """Submit a batch; return an opaque handle for polling."""
        ...

    def poll_batch(self, handle: BatchHandle) -> BatchStatus:
        """Check batch status without fetching results."""
        ...

    def fetch_results(self, handle: BatchHandle) -> Iterator[BatchResult]:
        """
        Yield results one-at-a-time as they arrive.

        Results are matched by request_id, never by position (ARCH §9.8 rule 1).
        """
        ...

    def create_context_cache(
        self,
        prefix: str,
        ttl_seconds: int = 3600,
    ) -> str:
        """
        Create a context cache from a stable prefix (Gemini only).

        Returns an opaque cache_handle to pass into subsequent complete_structured
        calls. Groq implementations must raise NotImplementedError.
        """
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class LLMError(Exception):
    """Base class for all LLM client errors."""


class LLMValidationError(LLMError):
    """
    Response could not be parsed into the requested Pydantic schema.
    Retryable (ST-11). Never coerce or swallow — treat as an error.
    """


class LLMRateLimitError(LLMError):
    """
    Provider returned 429. The client has already exhausted its retry budget.
    The caller should back off or pause (ARCH §9.8).
    """

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMSafetyBlockError(LLMError):
    """
    Provider refused to generate output due to content policy.
    Distinct from EMPTY — the reroute logic (T-P0-07) inspects this.
    """


class BudgetExceeded(Exception):
    """
    Hard cost ceiling reached (T-P0-10). Runner catches this to exit resumably.
    Not a crash — state is checkpointed before this is raised.
    """
