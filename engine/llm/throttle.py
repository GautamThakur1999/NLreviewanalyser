"""
T-P0-07 (partial) + T-P0-08 — Throttle utility shared by both LLM clients.

Token-bucket rate limiter and exponential backoff with Retry-After support.
Imported inside engine/llm/ only (ST-08).
"""

from __future__ import annotations

import logging
import random
import threading
import time
from typing import Callable, TypeVar

from engine.llm.base import LLMRateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TokenBucket:
    """
    Thread-safe token bucket for rate limiting.

    Controls both requests-per-minute (RPM) and tokens-per-minute (TPM).
    """

    def __init__(
        self,
        rpm: int | None = None,
        tpm: int | None = None,
        window_seconds: float = 60.0,
    ) -> None:
        self._rpm = rpm
        self._tpm = tpm
        self._window = window_seconds
        self._lock = threading.Lock()

        # Request bucket
        self._req_tokens = float(rpm) if rpm else float("inf")
        self._req_last = time.monotonic()

        # Token bucket (for TPM)
        self._tok_tokens = float(tpm) if tpm else float("inf")
        self._tok_last = time.monotonic()

    def _refill(self) -> None:
        """Refill buckets based on elapsed time (call under lock)."""
        now = time.monotonic()

        if self._rpm:
            elapsed = now - self._req_last
            added = elapsed * (self._rpm / self._window)
            self._req_tokens = min(float(self._rpm), self._req_tokens + added)
            self._req_last = now

        if self._tpm:
            elapsed = now - self._tok_last
            added = elapsed * (self._tpm / self._window)
            self._tok_tokens = min(float(self._tpm), self._tok_tokens + added)
            self._tok_last = now

    def acquire(self, token_count: int = 0) -> None:
        """
        Block until the bucket can accommodate token_count tokens + 1 request.
        """
        if self._tpm and token_count > self._tpm:
            logger.warning(f"Request token count ({token_count}) exceeds bucket TPM ({self._tpm}). Capping to {self._tpm}.")
            token_count = int(self._tpm)
            
        while True:
            with self._lock:
                self._refill()
                req_ok = self._req_tokens >= 1 or self._rpm is None
                tok_ok = self._tok_tokens >= token_count or self._tpm is None

                if req_ok and tok_ok:
                    if self._rpm:
                        self._req_tokens -= 1
                    if self._tpm and token_count:
                        self._tok_tokens -= token_count
                    return

            # Sleep a fraction of the window before retrying
            sleep_s = self._window / 10
            logger.debug("Rate-limit bucket full; sleeping %.1fs", sleep_s)
            time.sleep(sleep_s)


def with_backoff(
    fn: Callable[[], T],
    *,
    max_attempts: int = 7,
    base_delay: float = 8.0,
    max_delay: float = 120.0,
    jitter: bool = True,
) -> T:
    """
    Call fn() with exponential backoff on LLMRateLimitError.

    Respects the Retry-After header value when present (EC-M-09).
    All other exceptions propagate immediately.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except LLMRateLimitError as exc:
            last_exc = exc
            if attempt == max_attempts:
                break

            # Honour Retry-After if the provider gave one
            if exc.retry_after is not None:
                delay = min(exc.retry_after, max_delay)
            else:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

            if jitter:
                delay *= 0.5 + random.random() * 0.5  # noqa: S311

            logger.warning(
                "Rate limited (attempt %d/%d). Sleeping %.1fs.",
                attempt,
                max_attempts,
                delay,
            )
            time.sleep(delay)

    raise last_exc  # type: ignore[misc]
