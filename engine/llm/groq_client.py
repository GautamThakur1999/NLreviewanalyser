"""
T-P0-05 — Groq client implementation.

Implements LLMClient using the Groq SDK. Only file in the codebase that may
import from `groq` (ST-08 — enforced by pre-commit lint).

Responsibilities:
- Structured JSON output parsed into caller's Pydantic schema (ST-11)
- Token-bucket throttling keyed to configured TPM/RPM
- Exponential backoff honouring Retry-After on 429
- FinishReason surfacing — safety blocks → SAFETY_BLOCK, never EMPTY (EC-M-14)
- Token usage capture into StructuredResult.usage
- Batch path with request-ID-keyed results (ARCH §9.8 rule 1)

Guards: EC-M-17, EC-M-09
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Iterator

from pydantic import BaseModel, ValidationError

# ── VENDOR IMPORT — allowed here and ONLY here (ST-08) ──────────────────────
import groq as _groq
from groq import Groq as _Groq

from engine.llm.base import (
    BatchHandle,
    BatchRequest,
    BatchResult,
    BatchStatus,
    BudgetExceeded,
    FinishReason,
    LLMError,
    LLMRateLimitError,
    LLMSafetyBlockError,
    LLMValidationError,
    StructuredResult,
    TokenUsage,
)
from engine.llm.throttle import TokenBucket, with_backoff

logger = logging.getLogger(__name__)

# Groq finish-reason strings that signal a safety refusal
_GROQ_SAFETY_REASONS = frozenset({"content_filter", "content_policy_violation"})


def _map_finish_reason(raw: str | None) -> FinishReason:
    """
    Map Groq's finish_reason string to our enum.

    Safety blocks → SAFETY_BLOCK (never EMPTY). Unknown → ERROR.
    """
    if raw is None:
        return FinishReason.EMPTY
    r = raw.lower()
    if r == "stop":
        return FinishReason.COMPLETE
    if r in ("length", "max_tokens"):
        return FinishReason.TRUNCATED
    if r in _GROQ_SAFETY_REASONS:
        return FinishReason.SAFETY_BLOCK
    logger.warning("Unknown Groq finish_reason %r — mapped to ERROR", raw)
    return FinishReason.ERROR


class GroqClient:
    """
    Groq LLM client implementing the LLMClient protocol.

    Instantiate via the factory function make_groq_client() rather than directly,
    so the throttle is wired from config.
    """

    provider = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        rpm: int | None = None,
        tpm: int | None = None,
    ) -> None:
        self.model = model
        self._client = _Groq(api_key=api_key)
        self._throttle = TokenBucket(rpm=rpm, tpm=tpm)

    # ── Structured call ───────────────────────────────────────────────────────

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[BaseModel],
        cache_handle: str | None = None,  # noqa: ARG002 — Groq has no caching
        max_tokens: int = 2048,
    ) -> StructuredResult:
        """
        Single structured call with Pydantic validation (ST-11).

        Raises:
            LLMValidationError   if the response cannot be parsed — retryable
            LLMRateLimitError    on 429 after all retries
            LLMSafetyBlockError  on a content policy refusal
            LLMError             on other failures
        """
        import hashlib
        from pathlib import Path
        
        cache_key = hashlib.md5(f"{self.model}:{system}:{user}".encode("utf-8")).hexdigest()
        cache_file = Path("data") / "cache" / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
                parsed_obj = schema.model_validate(cached_data["parsed"])
                return StructuredResult(
                    parsed=parsed_obj,
                    usage=TokenUsage(),
                    finish_reason=FinishReason.COMPLETE,
                    raw=cached_data["raw"],
                    provider=self.provider,
                    model=self.model,
                )
            except Exception as e:
                logger.warning(f"Cache read failed, ignoring: {e}")

        # Estimate prompt tokens for throttle (rough: 1 token ≈ 4 chars)
        estimated_prompt_tokens = (len(system) + len(user)) // 4

        def _call() -> StructuredResult:
            self._throttle.acquire(token_count=estimated_prompt_tokens)
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                )
            except _groq.RateLimitError as exc:
                retry_after: float | None = None
                if hasattr(exc, "response") and exc.response is not None:
                    try:
                        retry_after = float(
                            exc.response.headers.get("Retry-After", 0)
                        )
                    except (ValueError, AttributeError):
                        pass
                raise LLMRateLimitError(str(exc), retry_after=retry_after) from exc
            except _groq.APIStatusError as exc:
                raise LLMError(f"Groq API error: {exc}") from exc

            choice = response.choices[0]
            finish_reason = _map_finish_reason(choice.finish_reason)

            # Surface safety blocks (EC-M-14)
            if finish_reason == FinishReason.SAFETY_BLOCK:
                raise LLMSafetyBlockError(
                    f"Groq safety block on model {self.model}. "
                    "finish_reason={choice.finish_reason!r}"
                )

            # Truncated responses are retryable with a smaller chunk (ARCH §9.8)
            if finish_reason == FinishReason.TRUNCATED:
                logger.warning(
                    "Groq response truncated (max_tokens=%d). "
                    "Caller should retry with smaller chunk.",
                    max_tokens,
                )

            raw_content = choice.message.content or ""

            # Parse & validate (ST-11 — never coerce on failure)
            try:
                parsed_dict = json.loads(raw_content)
                parsed_obj = schema.model_validate(parsed_dict)
            except (json.JSONDecodeError, ValidationError) as exc:
                raise LLMValidationError(
                    f"Failed to parse Groq response into {schema.__name__}: {exc}\n"
                    f"Raw response: {raw_content[:500]}"
                ) from exc

            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                cached_tokens=0,  # Groq has no context caching
            )

            result = StructuredResult(
                parsed=parsed_obj,
                usage=usage,
                finish_reason=finish_reason,
                raw=raw_content,
                provider=self.provider,
                model=self.model,
            )
            
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps({
                    "parsed": parsed_dict,
                    "raw": raw_content
                }, ensure_ascii=False), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
                
            return result

        return with_backoff(_call)

    # ── Batch path ────────────────────────────────────────────────────────────

    def submit_batch(self, requests: list[BatchRequest]) -> BatchHandle:
        """
        Submit multiple requests. Groq doesn't have a native async batch API,
        so we run them sequentially but return a handle that fetch_results
        can iterate over (stored in-memory).

        For production volume, callers should use complete_structured in a
        thread pool. This implementation satisfies the protocol contract.
        """
        handle_id = str(uuid.uuid4())
        # Store requests keyed by request_id for sequential execution
        self._pending_batches: dict[str, list[BatchRequest]] = getattr(
            self, "_pending_batches", {}
        )
        self._pending_batches[handle_id] = requests
        logger.info(
            "Groq batch submitted: handle=%s count=%d", handle_id, len(requests)
        )
        return BatchHandle(
            provider=self.provider,
            handle_id=handle_id,
            submitted_count=len(requests),
        )

    def poll_batch(self, handle: BatchHandle) -> BatchStatus:
        """Groq sequential batches are always immediately runnable."""
        pending = getattr(self, "_pending_batches", {})
        if handle.handle_id in pending:
            return BatchStatus.PENDING
        return BatchStatus.COMPLETE

    def fetch_results(self, handle: BatchHandle) -> Iterator[BatchResult]:
        """
        Execute each request and yield BatchResult keyed by request_id.

        Results are keyed by request_id, NEVER matched by position (ARCH §9.8).
        """
        pending = getattr(self, "_pending_batches", {})
        requests = pending.pop(handle.handle_id, [])

        for req in requests:
            # We need the actual schema class — callers must pass metadata
            # with "schema_class" set. In Phase 4, the label runner does this.
            schema_cls_name = req.schema_name
            schema_cls: type[BaseModel] | None = req.metadata.get("schema_class")
            if schema_cls is None:
                yield BatchResult(
                    request_id=req.request_id,
                    error=f"No schema_class in metadata for {schema_cls_name}",
                )
                continue

            try:
                result = self.complete_structured(
                    system=req.system,
                    user=req.user,
                    schema=schema_cls,
                )
                yield BatchResult(request_id=req.request_id, result=result)
            except Exception as exc:
                yield BatchResult(request_id=req.request_id, error=str(exc))

    def create_context_cache(self, prefix: str, ttl_seconds: int = 3600) -> str:
        """Groq has no context caching — raise clearly (ARCH §9.5)."""
        raise NotImplementedError(
            "Groq does not support context caching. "
            "Use GeminiClient for stages that require prefix caching."
        )
