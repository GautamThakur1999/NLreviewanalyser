"""
T-P2-05 - Product-review connector.

Collect category-level review text where publicly exposed.
Sets source=product_review, carries the category into meta.
Respects robots/ToS.
"""

from typing import Any, Iterator
from pathlib import Path
from datetime import datetime

from engine.collection.forum import ForumConnector

class ProductReviewConnector(ForumConnector):
    """
    Collects product reviews using CSS selectors.
    """
    
    def __init__(
        self,
        brand: str,
        data_dir: Path,
        base_url: str,
        selectors: dict[str, str],
        category: str,
        max_pages: int = 100,
    ):
        super().__init__(
            brand=brand,
            data_dir=data_dir,
            base_url=base_url,
            selectors=selectors,
            max_pages=max_pages
        )
        self.source = "product_review"
        self.category = category

    def collect(self, since: datetime | None, limit: int | None = None) -> Iterator[dict[str, Any]]:
        # We just wrap the parent collect and inject category
        for payload in super().collect(since, limit):
            payload["category"] = self.category
            payload["_source"] = self.source
            yield payload


def normalise_product_review_payload(raw: dict[str, Any], run_id: str, raw_payload_ref: str) -> "Verbatim":
    from engine.collection.forum import normalise_forum_payload
    
    # It shares the same structure as forum payload
    verbatim = normalise_forum_payload(raw, run_id, raw_payload_ref)
    
    # Inject category into meta
    if "category" in raw:
        verbatim.meta["category"] = raw["category"]
        
    return verbatim
