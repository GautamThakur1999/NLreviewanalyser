"""
T-P2-01 - App Store connector.

Public RSS review feed, paginated, locale-pinned; a snapshot not an archive.
Guards: EC-C-04
"""

import httpx
import logging
from datetime import datetime
from typing import Any, Iterator
from pathlib import Path

from engine.collection.base import BaseConnector, MaxPagesExceededError

logger = logging.getLogger(__name__)

class AppStoreConnector(BaseConnector):
    """
    Collects reviews from the Apple App Store via iTunes RSS feed.
    """
    
    def __init__(self, brand: str, data_dir: Path, app_id: str, locale: str = "in", max_pages: int = 10):
        # App Store RSS only goes up to page 10
        super().__init__(source="app_store", brand=brand, data_dir=data_dir, max_pages=min(max_pages, 10))
        self.app_id = app_id
        self.locale = locale
        self.client = httpx.Client(timeout=30.0)
        self.last_request = 0.0
        
    def __del__(self):
        try:
            self.client.close()
        except:
            pass
        
    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        page = 1
        yielded = 0
        seen_hashes = set()
        
        while page <= self.max_pages:
            url = f"https://itunes.apple.com/{self.locale}/rss/customerreviews/page={page}/id={self.app_id}/sortby=mostrecent/json"
            
            self.last_request = self.enforce_politeness(self.last_request, min_interval=1.0)
            
            try:
                logger.info(f"AppStoreConnector [{self.brand}]: fetching page {page}")
                resp = self.client.get(url)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"Failed to fetch App Store page {page} for {self.brand}: {e}")
                break
                
            feed = data.get("feed", {})
            entries = feed.get("entry", [])
            
            if not entries:
                logger.info(f"AppStoreConnector [{self.brand}]: no entries on page {page}, stopping.")
                break
                
            # The iTunes feed has the app itself as the first entry on page 1.
            # We filter it out (it usually doesn't have an author field with a name).
            reviews = [e for e in entries if "author" in e and "name" in e["author"]]
            
            if not reviews and page == 1:
                # Could be empty, or just no reviews
                pass
            
            # For loop detection we hash the entry IDs or content
            self.check_page_loop(entries, seen_hashes)
            
            for review in reviews:
                review["_pinned_locale"] = self.locale
                
                yield review
                yielded += 1
                if limit and yielded >= limit:
                    logger.info(f"AppStoreConnector [{self.brand}]: reached limit {limit}")
                    return
            
            page += 1
            
        if page > self.max_pages:
            logger.info(f"AppStoreConnector [{self.brand}]: reached max depth ({self.max_pages} pages). Depth cap documented.")


def normalise_app_store_review(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> "Verbatim":
    """
    Convert a raw App Store review to the Verbatim schema.
    """
    from engine.store.verbatim import make_verbatim
    from datetime import timezone
    
    # 1. Extract fields from the iTunes RSS format
    source_id = raw.get("id", {}).get("label")
    if not source_id:
        raise ValueError("Missing ID in App Store payload")
        
    author_name = raw.get("author", {}).get("name", {}).get("label", "unknown")
    text_raw = raw.get("content", {}).get("label", "")
    
    # Rating
    rating_str = raw.get("im:rating", {}).get("label", "")
    try:
        rating = int(rating_str)
        if rating < 1 or rating > 5:
            rating = None
    except ValueError:
        rating = None
        
    # Timestamp (App Store doesn't provide a precise timestamp in standard RSS json feed, but provides updated)
    # Actually, it might be in 'updated' -> 'label' (ISO format usually)
    updated_str = raw.get("updated", {}).get("label")
    if updated_str:
        try:
            # Typical format: 2024-03-24T05:27:12-07:00
            dt = datetime.fromisoformat(updated_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(tz=timezone.utc)
    else:
        dt = datetime.now(tz=timezone.utc)
        
    brand = raw.get("_brand", "unknown")
    locale = raw.get("_pinned_locale", "unknown")

    return make_verbatim(
        source="app_store",
        source_id=source_id,
        brand=brand,
        run_id=run_id,
        raw_payload_ref=raw_payload_ref,
        text_raw=text_raw,
        rating=rating,
        rating_scale=5,
        review_date=dt,
        meta={"userName": author_name, "locale": locale},
    )
