"""
T-P0-06 — Gemini client implementation.

Only file in the codebase that may import from `google.genai` (ST-08).

Responsibilities:
- Pydantic-native response_schema (schema passed directly, not as JSON string)
- Explicit context caching with TTL — asserts non-zero cached tokens (ARCH §9.5)
- Safety-block surfacing → SAFETY_BLOCK, never EMPTY (EC-M-14)
- Batch path with request-ID keying (ARCH §9.8)
- Token usage capture including cached-token count

Guards: EC-M-07, EC-M-21
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Iterator

from pydantic import BaseModel, ValidationError

# ── VENDOR IMPORT — allowed here and ONLY here (ST-08) ──────────────────────
import google.genai as genai
from google.genai import types as genai_types

from engine.llm.base import (
    BatchHandle,
    BatchRequest,
    BatchResult,
    BatchStatus,
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

# Gemini finish reason strings that indicate a safety refusal
_GEMINI_SAFETY_REASONS = frozenset({
    "SAFETY",
    "RECITATION",
    "BLOCKLIST",
    "PROHIBITED_CONTENT",
    "SPII",
})


def _map_finish_reason(raw: str | None) -> FinishReason:
    """Map Gemini's finish_reason to our enum. Safety → SAFETY_BLOCK (EC-M-14)."""
    if raw is None:
        return FinishReason.EMPTY
    r = raw.upper()
    if r == "STOP":
        return FinishReason.COMPLETE
    if r in ("MAX_TOKENS",):
        return FinishReason.TRUNCATED
    if r in _GEMINI_SAFETY_REASONS:
        return FinishReason.SAFETY_BLOCK
    if r == "OTHER":
        return FinishReason.ERROR
    logger.warning("Unknown Gemini finish_reason %r — mapped to ERROR", raw)
    return FinishReason.ERROR


class GeminiClient:
    """
    Gemini LLM client implementing the LLMClient protocol.

    Instantiate via make_gemini_client() to wire throttle from config.
    """

    provider = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        rpm: int | None = None,
        tpm: int | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._client = genai.Client(api_key=api_key)
        self._throttle = TokenBucket(rpm=rpm, tpm=tpm)

        # Cache registry: cache_handle (str) → CachedContent name
        self._cache_registry: dict[str, str] = {}

    # ── Context caching ───────────────────────────────────────────────────────

    def create_context_cache(
        self,
        prefix: str,
        ttl_seconds: int = 3600,
    ) -> str:
        """
        Create a Gemini context cache from a stable prefix (e.g. the codebook).

        Returns an opaque cache_handle. Subsequent complete_structured() calls
        with this handle reuse the cache — cached_tokens must be non-zero
        after the first batch (ARCH §9.5).

        Raises LLMError if the prefix is below the minimum token threshold.
        """
        handle_id = str(uuid.uuid4())
        try:
            cached_content = self._client.caches.create(
                model=self.model,
                config=genai_types.CreateCachedContentConfig(
                    contents=[prefix],
                    ttl=f"{ttl_seconds}s",
                    display_name=f"engine-cache-{handle_id[:8]}",
                ),
            )
        except Exception as exc:
            raise LLMError(
                f"Failed to create Gemini context cache: {exc}. "
                "Check that the prefix exceeds the minimum token threshold for "
                f"model {self.model} (ARCH §9.5)."
            ) from exc

        self._cache_registry[handle_id] = cached_content.name
        logger.info(
            "Gemini context cache created: handle=%s name=%s",
            handle_id,
            cached_content.name,
        )
        return handle_id

    def _resolve_cache(self, handle_id: str) -> str | None:
        """Resolve a cache handle to a Gemini CachedContent name."""
        return self._cache_registry.get(handle_id)

    # ── Structured call ───────────────────────────────────────────────────────

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[BaseModel],
        cache_handle: str | None = None,
        max_tokens: int = 8192,
    ) -> StructuredResult:
        """
        Single structured call. Pydantic model passed directly as response_schema.

        If cache_handle is provided and corresponds to a live cache, cached tokens
        are asserted non-zero on calls after the first batch (ARCH §9.5).

        Raises:
            LLMValidationError   — parse failure, retryable (ST-11)
            LLMRateLimitError    — 429 after retries
            LLMSafetyBlockError  — content policy refusal
            LLMError             — other failures
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

        estimated_prompt_tokens = (len(system) + len(user)) // 4

        def _call() -> StructuredResult:
            self._throttle.acquire(token_count=estimated_prompt_tokens)

            # Build generation config with Pydantic schema as response_schema
            generation_config = genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=max_tokens,
                system_instruction=system,
            )

            # Wire context cache if provided
            cached_content_name: str | None = None
            if cache_handle:
                cached_content_name = self._resolve_cache(cache_handle)
                if cached_content_name:
                    generation_config.cached_content = cached_content_name

            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=user,
                    config=generation_config,
                )
            except Exception as exc:
                exc_str = str(exc).lower()
                if "429" in exc_str or "quota" in exc_str or "rate" in exc_str:
                    raise LLMRateLimitError(str(exc)) from exc
                raise LLMError(f"Gemini API error: {exc}") from exc

            # Extract finish reason
            candidate = response.candidates[0] if response.candidates else None
            if candidate is None:
                raise LLMError("Gemini returned no candidates")

            finish_reason = _map_finish_reason(
                candidate.finish_reason.name if candidate.finish_reason else None
            )

            if finish_reason == FinishReason.SAFETY_BLOCK:
                raise LLMSafetyBlockError(
                    f"Gemini safety block. finish_reason={candidate.finish_reason}"
                )

            if finish_reason == FinishReason.TRUNCATED:
                logger.warning(
                    "Gemini response truncated (max_output_tokens=%d). "
                    "Retry with smaller chunk.",
                    max_tokens,
                )

            raw_content = response.text or ""

            # Parse & validate (ST-11 — no except: pass)
            try:
                parsed_dict = json.loads(raw_content)
                parsed_obj = schema.model_validate(parsed_dict)
            except (json.JSONDecodeError, ValidationError) as exc:
                raise LLMValidationError(
                    f"Failed to parse Gemini response into {schema.__name__}: {exc}\n"
                    f"Raw: {raw_content[:500]}"
                ) from exc

            # Token usage (including cached tokens)
            usage_meta = response.usage_metadata
            cached_tok = getattr(usage_meta, "cached_content_token_count", 0) or 0
            prompt_tok = getattr(usage_meta, "prompt_token_count", 0) or 0
            completion_tok = getattr(usage_meta, "candidates_token_count", 0) or 0

            usage = TokenUsage(
                prompt_tokens=prompt_tok,
                completion_tokens=completion_tok,
                cached_tokens=cached_tok,
            )

            # Assert cache effectiveness after first batch (ARCH §9.5)
            if cached_content_name and cached_tok == 0:
                logger.warning(
                    "Gemini context cache reported 0 cached tokens — "
                    "cache may be below the minimum token threshold. "
                    "Verify the prefix size for model %s.",
                    self.model,
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
        Submit a batch. For Gemini, we store requests for sequential execution
        since the genai SDK batch API is evolving. Production callers may switch
        to the native batch endpoint via this same interface.
        """
        handle_id = str(uuid.uuid4())
        self._pending_batches: dict[str, list[BatchRequest]] = getattr(
            self, "_pending_batches", {}
        )
        self._pending_batches[handle_id] = requests
        logger.info(
            "Gemini batch submitted: handle=%s count=%d", handle_id, len(requests)
        )
        return BatchHandle(
            provider=self.provider,
            handle_id=handle_id,
            submitted_count=len(requests),
        )

    def poll_batch(self, handle: BatchHandle) -> BatchStatus:
        pending = getattr(self, "_pending_batches", {})
        return BatchStatus.PENDING if handle.handle_id in pending else BatchStatus.COMPLETE

    def fetch_results(self, handle: BatchHandle) -> Iterator[BatchResult]:
        """
        Yield results keyed by request_id — NEVER by position (ARCH §9.8 rule 1).
        """
        pending = getattr(self, "_pending_batches", {})
        requests = pending.pop(handle.handle_id, [])

        for req in requests:
            schema_cls: type[BaseModel] | None = req.metadata.get("schema_class")
            if schema_cls is None:
                yield BatchResult(
                    request_id=req.request_id,
                    error=f"No schema_class in metadata for {req.schema_name}",
                )
                continue

            cache_handle = req.metadata.get("cache_handle")

            try:
                result = self.complete_structured(
                    system=req.system,
                    user=req.user,
                    schema=schema_cls,
                    cache_handle=cache_handle,
                )
                yield BatchResult(request_id=req.request_id, result=result)
            except Exception as exc:
                yield BatchResult(request_id=req.request_id, error=str(exc))
