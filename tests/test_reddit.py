import pytest
from datetime import datetime, timezone
from engine.collection.reddit import normalise_reddit_payload

def test_reddit_normaliser_submission():
    raw_payload = {
        "_type": "submission",
        "_source": "reddit",
        "_brand": "blinkit",
        "id": "12345",
        "subreddit": "india",
        "title": "Blinkit is fast",
        "selftext": "But it has high fees",
        "author": "user1",
        "created_utc": 1700000000,
        "score": 100,
        "permalink": "/r/india/comments/12345/blinkit_is_fast/",
        "query": "blinkit",
    }
    
    verbatim = normalise_reddit_payload(raw_payload, run_id="run1", raw_payload_ref="ref1")
    assert verbatim is not None
    assert verbatim.text_raw == "Blinkit is fast\n\nBut it has high fees"
    assert verbatim.rating is None
    assert verbatim.meta["author"] == "user1"

def test_reddit_normaliser_deleted_comment():
    raw_payload = {
        "_type": "comment",
        "_source": "reddit",
        "_brand": "blinkit",
        "id": "abcde",
        "subreddit": "india",
        "body": "[deleted]",
        "author": None,
        "created_utc": 1700000000,
        "score": 0,
        "permalink": "/r/india/comments/12345/blinkit_is_fast/abcde",
    }
    
    verbatim = normalise_reddit_payload(raw_payload, run_id="run1", raw_payload_ref="ref1")
    assert verbatim is None
