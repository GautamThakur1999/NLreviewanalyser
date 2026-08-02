"""
T-P1-05 - Play Store connector + normaliser.

Collects Play Store reviews across all 5 rating bands.
Writes raw payloads to archive.
Normalises to Verbatim schema.
EXPLICITLY DROPS `replyContent` (EC-C-17).

Guards: EC-C-17, EC-N-01, EC-N-03, EC-C-04
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from google_play_scraper import Sort, reviews

from engine.collection.base import BaseConnector
from engine.store.raw import RawArchiveWriter
from engine.store.verbatim import Verbatim, make_verbatim

logger = logging.getLogger(__name__)


class PlayStoreConnector(BaseConnector):
    """
    Play Store collection strategy:
    To bypass the "recent only" limitation, we sample across all 5 rating bands.
    Sort is always NEWEST to easily cut off at a `since` timestamp.
    """

    def __init__(
        self,
        brand: str,
        play_package: str,
        data_dir: Path,
        max_pages_per_band: int = 100,
        requests_per_minute: int = 30,
    ):
        super().__init__(source="play_store", brand=brand, data_dir=data_dir, max_pages=max_pages_per_band)
        self.play_package = play_package
        self.min_interval = 60.0 / requests_per_minute
        self._last_request_time = 0.0

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        """
        Yield raw review dicts from the Play Store.
        """
        total_yielded = 0
        
        # We iterate over each rating band (1 to 5)
        for rating in [1, 2, 3, 4, 5]:
            logger.info(f"Collecting Play Store reviews for {self.brand} (rating={rating}★)")
            continuation_token = None
            pages_fetched = 0
            seen_hashes: set[str] = set()

            while True:
                if limit and total_yielded >= limit:
                    return

                if self.max_pages and pages_fetched >= self.max_pages:
                    logger.info(f"Hit max_pages ({self.max_pages}) for rating {rating}")
                    break

                self._last_request_time = self.enforce_politeness(self._last_request_time, self.min_interval)

                try:
                    page_reviews, continuation_token = reviews(
                        self.play_package,
                        lang="en",
                        country="in",
                        sort=Sort.NEWEST,
                        count=100,
                        filter_score_with=rating,
                        continuation_token=continuation_token,
                    )
                except Exception as e:
                    logger.error(f"Error fetching Play Store reviews: {e}")
                    break

                pages_fetched += 1
                if not page_reviews:
                    break

                self.check_page_loop(page_reviews, seen_hashes)

                # Process reviews
                all_older = True
                for review in page_reviews:
                    # review['at'] is a naive datetime in local timezone (usually).
                    # google_play_scraper returns datetime objects.
                    dt = review.get("at")
                    if isinstance(dt, datetime):
                        # Assume UTC for now
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    
                    if since and dt and dt < since:
                        # Found a review older than `since`.
                        continue
                    else:
                        all_older = False
                        
                    # We inject the rating scale here as part of raw just in case
                    review["_source"] = self.source
                    review["_brand"] = self.brand
                    
                    yield review
                    total_yielded += 1
                    
                    if limit and total_yielded >= limit:
                        return

                if all_older:
                    # All reviews on this page are older than `since`. We can stop this rating band.
                    logger.info(f"Reached `since` boundary for rating {rating}")
                    break

                if not continuation_token:
                    break


def normalise_play_store_review(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> Verbatim:
    """
    Convert a raw Play Store review to the Verbatim schema.
    Explicitly drops `replyContent` (EC-C-17).
    """
    # Defensive copy to avoid mutating the original raw dict
    data = raw.copy()
    
    # 1. Drop dev reply (EC-C-17)
    _ = data.pop("replyContent", None)
    _ = data.pop("repliedAt", None)

    # 2. Extract timestamp
    dt = data.get("at")
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Fallback if it's not a datetime for some reason
        dt = datetime.now(tz=timezone.utc)

    # 3. Construct the Verbatim
    source = data.get("_source", "play_store")
    brand = data.get("_brand", "unknown")
    source_id = data.get("reviewId")
    if not source_id:
        raise ValueError("Missing reviewId in Play Store payload")

    text_raw = data.get("content") or ""
    rating = data.get("score")
    thumbs_up = data.get("thumbsUpCount") or 0

    return make_verbatim(
        source=source,
        source_id=source_id,
        brand=brand,
        run_id=run_id,
        raw_payload_ref=raw_payload_ref,
        text_raw=text_raw,
        rating=rating,
        rating_scale=5,
        review_date=dt,
        helpful_votes=thumbs_up,
        thumbs_up=thumbs_up,
        meta={"userName": data.get("userName"), "userImage": data.get("userImage")},
    )
