import json
import pytest
from pathlib import Path
from engine.clean.dedup import deduplicate
from engine.store.verbatim import Verbatim
from engine.normalise.text import content_hash, simhash, verbatim_id

def test_dedup():
    fixture_path = Path(__file__).parent / "fixtures" / "duplicate_cluster.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    verbatims = []
    for i, d in enumerate(data):
        # Fill in missing fields for Verbatim
        v_dict = d.copy()
        v_dict["source_id"] = d["verbatim_id"]
        v_dict["verbatim_id"] = verbatim_id(v_dict["source"], v_dict["source_id"])
        v_dict["run_id"] = "r1"
        v_dict["raw_payload_ref"] = "ref"
        v_dict["content_hash"] = content_hash(d["text_clean"])
        v_dict["simhash"] = simhash(d["text_clean"])
        v_dict["rating"] = 5
        v_dict["rating_scale"] = 5
        v_dict["lang"] = "en"
        
        # Only testing dedup logic, so missing some fields won't hurt if we create via parse_obj or manually
        # But Verbatim might have strict validation, let's just create it:
        v = Verbatim(
            verbatim_id=v_dict["verbatim_id"],
            source=v_dict["source"],
            source_id=v_dict["source_id"],
            brand=v_dict["brand"],
            run_id=v_dict["run_id"],
            raw_payload_ref=v_dict["raw_payload_ref"],
            text_raw=v_dict["text_raw"],
            text_clean=v_dict["text_clean"],
            content_hash=v_dict["content_hash"],
            simhash=v_dict["simhash"],
            author_hash=v_dict["author_hash"],
        )
        verbatims.append(v)
        
    # Test scoping: Should raise error if cross-brand
    with pytest.raises(ValueError, match="must be scoped within a single"):
        deduplicate(verbatims)
        
    # Isolate blinkit
    blinkit_verbatims = [v for v in verbatims if v.brand == "blinkit"]
    
    # Expected: 
    # v1 (Good app, authorA) - kept
    # v2 (Good app, authorB) - kept (short, diff author)
    # v3 (Good app, authorA) - collapsed into v1 (short, same author)
    # v5 (long review, authorD) - kept
    # v6 (long review, authorE) - collapsed into v5 (near match, long)
    
    deduped = deduplicate(blinkit_verbatims)
    
    assert len(deduped) == 3
    
    v1_id = verbatim_id("play_store", "v1")
    v2_id = verbatim_id("play_store", "v2")
    v3_id = verbatim_id("play_store", "v3")
    v5_id = verbatim_id("play_store", "v5")
    v6_id = verbatim_id("play_store", "v6")

    ids = [v.verbatim_id for v in deduped]
    assert v1_id in ids
    assert v2_id in ids
    assert v3_id not in ids
    assert v5_id in ids
    assert v6_id not in ids
    
    # Check duplicate counts
    v1 = next(v for v in deduped if v.verbatim_id == v1_id)
    assert v1.duplicate_count == 2 # Initial count is 1. +1 from v3 -> 2.
    
    v5 = next(v for v in deduped if v.verbatim_id == v5_id)
    assert v5.duplicate_count == 2
