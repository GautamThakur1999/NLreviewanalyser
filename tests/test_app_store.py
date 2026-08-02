import pytest
from datetime import datetime, timezone
from pathlib import Path

from engine.collection.app_store import normalise_app_store_review

def test_app_store_normaliser():
    raw_payload = {
        "id": {"label": "123456789"},
        "author": {"name": {"label": "John Doe"}},
        "content": {"label": "Great app, highly recommend!"},
        "im:rating": {"label": "5"},
        "updated": {"label": "2024-03-24T05:27:12-07:00"},
        "_brand": "blinkit",
        "_pinned_locale": "in",
    }
    
    verbatim = normalise_app_store_review(raw_payload, run_id="test_run", raw_payload_ref="ref")
    
    assert verbatim.source == "app_store"
    assert verbatim.brand == "blinkit"
    assert verbatim.source_id == "123456789"
    assert verbatim.text_raw == "Great app, highly recommend!"
    assert verbatim.rating == 5
    assert verbatim.rating_scale == 5
    assert verbatim.review_date == datetime.fromisoformat("2024-03-24T05:27:12-07:00").astimezone(timezone.utc)
    assert verbatim.meta["userName"] == "John Doe"
    assert verbatim.meta["locale"] == "in"
    
def test_app_store_normaliser_missing_optional_fields():
    raw_payload = {
        "id": {"label": "987"},
        "_brand": "swiggy",
    }
    
    verbatim = normalise_app_store_review(raw_payload, run_id="test_run", raw_payload_ref="ref")
    assert verbatim.source_id == "987"
    assert verbatim.text_raw == ""
    assert verbatim.rating is None
    assert verbatim.meta["userName"] == "unknown"
    assert verbatim.meta["locale"] == "unknown"
