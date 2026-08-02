"""
T-P1-06 - Minimum-expected-count guard.

Asserts count >= min_expected. Falls back to explicit acknowledgement.
Guards: EC-C-10
"""

import logging

logger = logging.getLogger(__name__)


class LowCountError(Exception):
    """Raised when collected count falls below min_expected."""
    pass


def check_min_count(
    source: str, brand: str, count: int, min_expected: int, acknowledged: bool
) -> None:
    """
    Check if the collected count meets the minimum expected floor (EC-C-10).
    If it fails, raises LowCountError unless acknowledged is True.
    """
    if count >= min_expected:
        logger.info(f"✓ {source}/{brand} count ({count}) meets minimum ({min_expected})")
        return

    if acknowledged:
        logger.warning(
            f"⚠ {source}/{brand} count ({count}) below minimum ({min_expected}), "
            "but explicitly acknowledged. Proceeding."
        )
        return

    raise LowCountError(
        f"Collected count {count} for {source}/{brand} is below the expected minimum of {min_expected}. "
        f"This usually indicates a broken collector or empty payload. "
        f"To proceed anyway, run with --acknowledge-low {source}"
    )
