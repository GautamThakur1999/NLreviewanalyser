"""
Tests for T-P1-01 — Verbatim schema.

Guards: EC-N-10, EC-D-06
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from engine.store.verbatim import (
    Verbatim,
    assert_unique_ids,
    make_verbatim,
)
from engine.normalise.text import normalise_text


class TestVerbatimSchema:
    def test_make_verbatim_derives_fields_correctly(self):
        text_raw = "Hello \u200b world! \r\n This is great."
        v = make_verbatim(
            source="play_store",
            source_id="review_123",
            brand="blinkit",
            run_id="run_01",
            raw_payload_ref="run_01/play_store_blinkit.jsonl.gz#L1",
            text_raw=text_raw,
            rating=5,
        )
        
        assert v.source == "play_store"
        assert v.source_id == "review_123"
        assert len(v.verbatim_id) == 16
        
        # text_clean must be normalised
        expected_clean = normalise_text(text_raw)
        assert v.text_clean == expected_clean
        assert "\u200b" not in v.text_clean
        assert "\r" not in v.text_clean
        
        # Hashes should be populated
        assert len(v.content_hash) == 64
        assert isinstance(v.simhash, int)
        
        # Defaults
        assert v.rating_scale == 5
        assert v.lang == "unknown"
        assert v.helpful_votes == 0

    def test_direct_instantiation_validates_text_clean(self):
        # Using a raw string that isn't normalised should fail
        raw = "unnormalised \r\n string"
        with pytest.raises(ValidationError, match="text_clean is not the output of normalise_text"):
            Verbatim(
                verbatim_id="0123456789abcdef",
                source="test",
                source_id="1",
                brand="test",
                run_id="r1",
                raw_payload_ref="ref",
                collected_at=datetime.now(tz=timezone.utc),
                text_raw=raw,
                text_clean=raw,  # Intentional error: not normalised
                content_hash="hash",
                simhash=0,
            )

    def test_direct_instantiation_validates_id_format(self):
        clean = "clean text"
        with pytest.raises(ValidationError, match="verbatim_id must be a 16-char hex string"):
            Verbatim(
                verbatim_id="not_hex_or_16_chars",
                source="test",
                source_id="1",
                brand="test",
                run_id="r1",
                raw_payload_ref="ref",
                collected_at=datetime.now(tz=timezone.utc),
                text_raw=clean,
                text_clean=clean,
                content_hash="hash",
                simhash=0,
            )

    def test_verbatim_is_immutable(self):
        v = make_verbatim(
            source="test", source_id="1", brand="test", run_id="r1",
            raw_payload_ref="ref", text_raw="text"
        )
        with pytest.raises(ValidationError, match="Instance is frozen"):
            v.rating = 4

    def test_id_stability(self):
        # Same source + source_id -> same verbatim_id across calls
        v1 = make_verbatim(
            source="play_store", source_id="id1", brand="b1", run_id="r1",
            raw_payload_ref="ref1", text_raw="t1"
        )
        v2 = make_verbatim(
            source="play_store", source_id="id1", brand="b2", run_id="r2",
            raw_payload_ref="ref2", text_raw="t2"
        )
        assert v1.verbatim_id == v2.verbatim_id

    def test_rating_validation(self):
        with pytest.raises(ValidationError, match="rating must be 1-5"):
            make_verbatim(
                source="test", source_id="1", brand="test", run_id="r1",
                raw_payload_ref="ref", text_raw="text", rating=6
            )


class TestAssertUniqueIds:
    def test_unique_ids_pass(self):
        v1 = make_verbatim(
            source="test", source_id="1", brand="test", run_id="r1",
            raw_payload_ref="ref", text_raw="text"
        )
        v2 = make_verbatim(
            source="test", source_id="2", brand="test", run_id="r1",
            raw_payload_ref="ref", text_raw="text"
        )
        assert_unique_ids([v1, v2])  # Should not raise

    def test_duplicate_ids_fail(self):
        v1 = make_verbatim(
            source="test", source_id="1", brand="test", run_id="r1",
            raw_payload_ref="ref", text_raw="text"
        )
        v2 = make_verbatim(
            source="test", source_id="1", brand="test", run_id="r1",
            raw_payload_ref="ref", text_raw="text"
        )
        with pytest.raises(ValueError, match="Duplicate verbatim_id detected"):
            assert_unique_ids([v1, v2])
