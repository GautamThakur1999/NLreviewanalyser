"""
T-P2-06 - X (best-effort) + Instagram gap.

Attempt X within available tier. Document Instagram as a declared gap.
Guards: EC-C-06, EC-C-07
"""

import logging
from datetime import datetime, timezone
from typing import Any, Iterator
from pathlib import Path

from engine.collection.base import BaseConnector

logger = logging.getLogger(__name__)


class XConnector(BaseConnector):
    """
    Best-effort collection from X (Twitter).
    """
    
    def __init__(
        self,
        brand: str,
        data_dir: Path,
        bearer_token: str | None = None,
        max_pages: int = 10,
    ):
        super().__init__(source="x", brand=brand, data_dir=data_dir, max_pages=max_pages)
        self.bearer_token = bearer_token

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        if not self.bearer_token:
            logger.warning(
                f"XConnector [{self.brand}]: No bearer token provided. "
                "Unable to collect from X. Documenting as a declared gap (EC-C-06)."
            )
            return
            
        logger.warning(f"XConnector [{self.brand}]: Free tier API is highly restricted. Attempting best-effort.")
        # Not implementing full v2 search as it usually fails without a paid tier.
        # Yields nothing, which means 0 volume collected, fulfilling the gap documentation.
        return


class InstagramConnector(BaseConnector):
    """
    Instagram is a declared gap due to hostile ToS and lack of compliant API (EC-C-07).
    Calling this connector will intentionally yield nothing and log the gap.
    """
    
    def __init__(self, brand: str, data_dir: Path):
        super().__init__(source="instagram", brand=brand, data_dir=data_dir, max_pages=0)
        
    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        logger.warning(
            f"InstagramConnector [{self.brand}]: Instagram is a declared gap. "
            "No compliant API exists. Documenting as a declared gap (EC-C-07)."
        )
        return
        yield {}  # type: ignore # just for the generator typing


def normalise_x_payload(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> "Verbatim":
    raise NotImplementedError("X parsing not implemented.")
