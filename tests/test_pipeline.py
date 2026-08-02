import pytest
from pathlib import Path

from engine.store.verbatim import Verbatim
from engine.clean.pipeline import apply_cleaning_chain
from engine.normalise.text import verbatim_id

def test_reconciliation_invariant(tmp_path):
    # Create some mock verbatims
    v1 = Verbatim(
        verbatim_id=verbatim_id("play_store", "1"),
        source="play_store", source_id="1", brand="blinkit", run_id="r1", raw_payload_ref="ref",
        text_raw="Good app", text_clean="Good app",
        content_hash="mock1", simhash=1, author_hash="a1",
        rating=5, rating_scale=5, lang="en"
    )
    v2 = Verbatim( # Exact duplicate of v1, same author
        verbatim_id=verbatim_id("play_store", "2"),
        source="play_store", source_id="2", brand="blinkit", run_id="r1", raw_payload_ref="ref",
        text_raw="Good app", text_clean="Good app",
        content_hash="mock1", simhash=1, author_hash="a1",
        rating=5, rating_scale=5, lang="en"
    )
    v3 = Verbatim( # Spam
        verbatim_id=verbatim_id("play_store", "3"),
        source="play_store", source_id="3", brand="blinkit", run_id="r1", raw_payload_ref="ref",
        text_raw="Please use my code X123", text_clean="Please use my code X123",
        content_hash="mock3", simhash=3, author_hash="a3",
        rating=5, rating_scale=5, lang="en"
    )
    v4 = Verbatim( # Empty
        verbatim_id=verbatim_id("play_store", "4"),
        source="play_store", source_id="4", brand="blinkit", run_id="r1", raw_payload_ref="ref",
        text_raw="   ", text_clean="",
        content_hash="mock4", simhash=4, author_hash="a4",
        rating=5, rating_scale=5, lang="en"
    )
    v5 = Verbatim( # Normal long review
        verbatim_id=verbatim_id("play_store", "5"),
        source="play_store", source_id="5", brand="blinkit", run_id="r1", raw_payload_ref="ref",
        text_raw="This app is really good and I use it daily.", text_clean="This app is really good and I use it daily.",
        content_hash="mock5", simhash=5, author_hash="a5",
        rating=5, rating_scale=5, lang="en"
    )

    verbatims = [v1, v2, v3, v4, v5]
    
    clean, quarantined, collapsed = apply_cleaning_chain(verbatims, tmp_path)
    
    assert len(verbatims) == len(clean) + len(quarantined) + collapsed
    
    assert len(clean) == 2 # v1 (v2 collapsed into it) and v5
    assert len(quarantined) == 2 # v3 and v4
    assert collapsed == 1 # v2

    # Assert PII logic didn't fail
    v1_clean = next(v for v in clean if v.verbatim_id == v1.verbatim_id)
    assert v1_clean.duplicate_count == 2
