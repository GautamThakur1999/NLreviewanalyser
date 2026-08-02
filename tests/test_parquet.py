"""
Tests for T-P1-07 — Parquet writer.

Guards: EC-X-03, EC-X-05
"""

import pyarrow.parquet as pq

from engine.store.parquet import write_verbatims_to_parquet
from engine.store.verbatim import make_verbatim


class TestParquetWriter:
    def test_writes_atomic_parquet(self, tmp_path):
        v1 = make_verbatim(
            source="play_store",
            source_id="1",
            brand="blinkit",
            run_id="run_1",
            raw_payload_ref="ref1",
            text_raw="hello",
            rating=5,
        )
        v2 = make_verbatim(
            source="play_store",
            source_id="2",
            brand="blinkit",
            run_id="run_1",
            raw_payload_ref="ref2",
            text_raw="world",
            rating=4,
        )
        
        path = write_verbatims_to_parquet([v1, v2], tmp_path, "run_1")
        
        assert path.exists()
        assert "source=play_store" in str(path)
        assert "brand=blinkit" in str(path)
        
        # Read back (using file-like object to bypass PyArrow dataset partition discovery from path)
        with open(path, "rb") as f:
            table = pq.read_table(f)
        assert table.num_rows == 2
        
        ids = table.column("verbatim_id").to_pylist()
        assert v1.verbatim_id in ids
        assert v2.verbatim_id in ids
        
        ratings = table.column("rating").to_pylist()
        assert 5 in ratings
        assert 4 in ratings
