"""
Tests for T-P1-03 — Connector base class.

Guards: EC-C-11, EC-C-12, EC-C-13
"""

from datetime import datetime, timezone

import pytest

from engine.collection.base import BaseConnector, PageLoopError


class TestBaseConnector:
    def test_watermark_load_save(self, tmp_path):
        connector = BaseConnector("test_src", "test_brand", tmp_path)
        
        # Initially none
        assert connector.load_watermark() is None
        
        # Save one
        dt = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        connector.save_watermark(dt)
        
        # Load it
        loaded = connector.load_watermark()
        assert loaded == dt
        
        # Save an older one - should not overwrite
        older = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        connector.save_watermark(older)
        assert connector.load_watermark() == dt
        
        # Save a newer one - should overwrite
        newer = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        connector.save_watermark(newer)
        assert connector.load_watermark() == newer

    def test_page_loop_detection(self, tmp_path):
        connector = BaseConnector("test", "test", tmp_path)
        seen = set()
        
        page1 = [{"id": 1}]
        page2 = [{"id": 2}]
        
        connector.check_page_loop(page1, seen)
        connector.check_page_loop(page2, seen)
        
        # Re-sending page1 should raise
        with pytest.raises(PageLoopError, match="Paginator loop detected"):
            connector.check_page_loop(page1, seen)
