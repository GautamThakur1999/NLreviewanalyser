"""
T-P1-03 - Connector protocol + base class.

Provides shared politeness (rate limiting, backoff), watermark tracking,
and page-loop safety for all collectors.

Guards: EC-C-11, EC-C-12, EC-C-13
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Protocol

from engine.llm.throttle import with_backoff

logger = logging.getLogger(__name__)


class Connector(Protocol):
    """
    Protocol for all data collectors (ARCH §5.1).
    """

    @property
    def source(self) -> str:
        ...

    @property
    def brand(self) -> str:
        ...

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        """
        Yield raw payloads (dicts) representing collected documents.
        """
        ...


class PageLoopError(Exception):
    """Raised when a paginator fails to advance (EC-C-12)."""
    pass


class MaxPagesExceededError(Exception):
    """Raised when max_pages is hit (EC-C-13)."""
    pass


class BaseConnector:
    """
    Base class providing watermark tracking and page-loop safety.
    Subclasses should implement `_fetch_page()`.
    """
    
    def __init__(self, source: str, brand: str, data_dir: Path, max_pages: int = 100):
        self.source = source
        self.brand = brand
        self.data_dir = data_dir
        self.max_pages = max_pages
        
        self.watermark_dir = data_dir / "watermarks"
        self.watermark_dir.mkdir(parents=True, exist_ok=True)
        self.watermark_file = self.watermark_dir / f"{source}_{brand}.json"

    def load_watermark(self) -> datetime | None:
        """Load the high watermark (latest collected timestamp)."""
        if not self.watermark_file.exists():
            return None
        try:
            data = json.loads(self.watermark_file.read_text(encoding="utf-8"))
            ts = data.get("high_watermark")
            if ts:
                return datetime.fromisoformat(ts).astimezone(timezone.utc)
        except Exception as e:
            logger.warning(f"Failed to load watermark for {self.source}/{self.brand}: {e}")
        return None

    def save_watermark(self, latest_ts: datetime) -> None:
        """Save the new high watermark."""
        # Only advance the watermark, never go backwards
        current = self.load_watermark()
        if current and latest_ts < current:
            return
            
        data = {"high_watermark": latest_ts.isoformat()}
        # Atomic write
        temp_file = self.watermark_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data), encoding="utf-8")
        temp_file.replace(self.watermark_file)

    def _page_hash(self, page_data: Any) -> str:
        """Hash the page content to detect loops (EC-C-12)."""
        raw = json.dumps(page_data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check_page_loop(self, page_data: Any, seen_hashes: set[str]) -> None:
        """
        Assert the page hasn't been seen before.
        Adds the current page hash to seen_hashes.
        """
        h = self._page_hash(page_data)
        if h in seen_hashes:
            raise PageLoopError(f"Paginator loop detected: page hash {h} already seen.")
        seen_hashes.add(h)

    def enforce_politeness(self, last_request_time: float, min_interval: float) -> float:
        """
        Sleep if necessary to ensure min_interval between requests.
        Returns the new last_request_time.
        """
        now = time.monotonic()
        elapsed = now - last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        return time.monotonic()
