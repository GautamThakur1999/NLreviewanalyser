"""
Tests for T-P1-05 — Play Store connector and normaliser.

Guards: EC-C-17
"""

from datetime import datetime, timezone

from engine.collection.play_store import normalise_play_store_review


class TestPlayStoreNormaliser:
    def test_drops_dev_reply(self):
        raw_payload = {
            "reviewId": "gp:123456",
            "userName": "Test User",
            "content": "App is broken",
            "score": 1,
            "thumbsUpCount": 5,
            "at": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "replyContent": "Sorry to hear that, please email us.",
            "repliedAt": datetime(2025, 1, 2, tzinfo=timezone.utc),
        }
        
        v = normalise_play_store_review(raw_payload, "run_01", "ref")
        
        # Verify core fields
        assert v.source == "play_store"
        assert v.source_id == "gp:123456"
        assert v.text_raw == "App is broken"
        assert v.rating == 1
        assert v.thumbs_up == 5
        
        # Guard EC-C-17: replyContent must not be in text_raw, text_clean, or meta
        assert "Sorry" not in v.text_raw
        assert "Sorry" not in v.text_clean
        assert "replyContent" not in v.meta
        assert "repliedAt" not in v.meta

    def test_handles_missing_fields(self):
        raw_payload = {
            "reviewId": "gp:111",
            # missing content, score, thumbsUpCount, etc.
        }
        
        v = normalise_play_store_review(raw_payload, "run_01", "ref")
        
        assert v.source_id == "gp:111"
        assert v.text_raw == ""
        assert v.rating is None
        assert v.thumbs_up == 0
