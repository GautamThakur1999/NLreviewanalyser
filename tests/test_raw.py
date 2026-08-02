"""
Tests for T-P1-02 — Raw archive writer.

Guards: EC-C-16, EC-C-14
"""

import gzip
import json

from engine.store.raw import RawArchiveWriter
from engine.store.verbatim import make_verbatim


class TestRawArchiveWriter:
    def test_writes_to_gzip_jsonl(self, tmp_path):
        payload1 = {"id": "1", "text": "hello"}
        payload2 = {"id": "2", "text": "world"}
        
        with RawArchiveWriter("run_01", "play_store", "blinkit", tmp_path) as writer:
            ref1 = writer.write_payload(payload1)
            ref2 = writer.write_payload(payload2)
            
        assert ref1 == "run_01/play_store_blinkit.jsonl.gz#L1"
        assert ref2 == "run_01/play_store_blinkit.jsonl.gz#L2"
        
        archive_path = tmp_path / "raw" / "run_01" / "play_store_blinkit.jsonl.gz"
        assert archive_path.exists()
        
        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            lines = f.readlines()
            
        assert len(lines) == 2
        assert json.loads(lines[0]) == payload1
        assert json.loads(lines[1]) == payload2

    def test_renormalisation_reproduces_identical_verbatim(self, tmp_path):
        payload = {
            "source": "play_store",
            "source_id": "rev_1",
            "brand": "blinkit",
            "text": "café\r\nand zero\u200bwidth",
            "rating": 5
        }
        
        # Original generation
        v1 = make_verbatim(
            source=payload["source"],
            source_id=payload["source_id"],
            brand=payload["brand"],
            run_id="run_02",
            raw_payload_ref="ref",
            text_raw=payload["text"],
            rating=payload["rating"],
        )
        
        # Write to archive
        with RawArchiveWriter("run_02", payload["source"], payload["brand"], tmp_path) as writer:
            writer.write_payload(payload)
            
        # Re-read and generate
        archive_path = tmp_path / "raw" / "run_02" / "play_store_blinkit.jsonl.gz"
        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            read_payload = json.loads(f.readline())
            
        v2 = make_verbatim(
            source=read_payload["source"],
            source_id=read_payload["source_id"],
            brand=read_payload["brand"],
            run_id="run_02",
            raw_payload_ref="ref",
            text_raw=read_payload["text"],
            rating=read_payload["rating"],
        )
        
        assert v1.verbatim_id == v2.verbatim_id
        assert v1.text_clean == v2.text_clean
        assert v1.content_hash == v2.content_hash
