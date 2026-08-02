"""
T-P2-04 - YouTube connector.

Data API v3 commentThreads; quota-aware; disabled-comments handled.
Guards: EC-C-08
"""

import logging
from datetime import datetime, timezone
from typing import Any, Iterator
from pathlib import Path

import httpx

from engine.collection.base import BaseConnector

logger = logging.getLogger(__name__)


class YouTubeConnector(BaseConnector):
    """
    Collects comments from YouTube videos using the Data API v3.
    """
    
    def __init__(
        self,
        brand: str,
        data_dir: Path,
        api_key: str,
        video_ids: list[str],
        max_pages: int = 100,
    ):
        super().__init__(source="youtube", brand=brand, data_dir=data_dir, max_pages=max_pages)
        self.api_key = api_key
        self.video_ids = video_ids
        self.client = httpx.Client(timeout=30.0)
        self.last_request = 0.0

    def __del__(self):
        try:
            self.client.close()
        except:
            pass

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        yielded = 0
        
        for video_id in self.video_ids:
            page_token = ""
            pages_fetched = 0
            seen_hashes = set()
            
            while pages_fetched < self.max_pages:
                self.last_request = self.enforce_politeness(self.last_request, min_interval=0.5)
                
                url = "https://www.googleapis.com/youtube/v3/commentThreads"
                params = {
                    "part": "snippet,replies",
                    "videoId": video_id,
                    "key": self.api_key,
                    "maxResults": 100,
                    "textFormat": "plainText",
                }
                if page_token:
                    params["pageToken"] = page_token
                    
                try:
                    logger.info(f"YouTubeConnector [{self.brand}]: fetching video {video_id} page {pages_fetched+1}")
                    resp = self.client.get(url, params=params)
                    
                    if resp.status_code == 403 and "quotaExceeded" in resp.text:
                        # Pause cleanly on quota exhaustion (EC-C-08)
                        logger.error("YouTube API quota exceeded. Pausing cleanly.")
                        return
                        
                    if resp.status_code == 403 and "disabled comments" in resp.text.lower():
                        logger.warning(f"Comments disabled for video {video_id}. Skipping.")
                        break
                        
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"Failed to fetch YouTube comments for video {video_id}: {e}")
                    break
                    
                items = data.get("items", [])
                if not items:
                    break
                    
                self.check_page_loop(items, seen_hashes)
                
                for item in items:
                    if limit and yielded >= limit:
                        return
                        
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    
                    # Check since
                    published_at = snippet.get("publishedAt")
                    if published_at:
                        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                        if since and dt < since:
                            continue
                            
                    payload = {
                        "_source": self.source,
                        "_brand": self.brand,
                        "video_id": video_id,
                        "item": item,
                    }
                    yield payload
                    yielded += 1
                    
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
                    
                pages_fetched += 1


def normalise_youtube_payload(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> "Verbatim":
    from engine.store.verbatim import make_verbatim
    
    source = raw.get("_source", "youtube")
    brand = raw.get("_brand", "unknown")
    
    item = raw.get("item", {})
    toplevel = item.get("snippet", {}).get("topLevelComment", {})
    snippet = toplevel.get("snippet", {})
    
    source_id = toplevel.get("id")
    if not source_id:
        raise ValueError("Missing id in YouTube payload")
        
    text_raw = snippet.get("textDisplay", "")
    author = snippet.get("authorDisplayName", "unknown")
    like_count = snippet.get("likeCount", 0)
    
    published_at = snippet.get("publishedAt")
    if published_at:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    else:
        dt = datetime.now(tz=timezone.utc)
        
    video_id = raw.get("video_id", "unknown")
        
    return make_verbatim(
        source=source,
        source_id=source_id,
        brand=brand,
        run_id=run_id,
        raw_payload_ref=raw_payload_ref,
        text_raw=text_raw,
        rating=None,
        review_date=dt,
        helpful_votes=like_count,
        thumbs_up=like_count,
        meta={"author": author, "video_id": video_id}
    )
