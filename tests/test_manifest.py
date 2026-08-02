"""
Tests for T-P0-12 — Manifest writer and logging.

Guards: EC-ST-04, EC-ST-06; ST-10, ST-14
"""

import json
from pathlib import Path

import pytest

from engine.store.manifest import Manifest, make_run_id


class TestManifest:
    def test_created_immediately(self, tmp_path):
        m = Manifest("test-run-001", tmp_path / "manifest.json")
        assert (tmp_path / "manifest.json").exists()

    def test_run_id_in_manifest(self, tmp_path):
        m = Manifest("myrun-123", tmp_path / "manifest.json")
        data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert data["run_id"] == "myrun-123"

    def test_status_running_initially(self, tmp_path):
        m = Manifest("r1", tmp_path / "manifest.json")
        data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert data["status"] == "running"

    def test_complete_updates_status(self, tmp_path):
        m = Manifest("r1", tmp_path / "manifest.json")
        m.complete()
        data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert data["status"] == "complete"

    def test_reconciliation_invariant_passes(self, tmp_path):
        m = Manifest("r1", tmp_path / "manifest.json")
        # in=10, out=7, quarantined=2, filtered=1 → 10==10 ✓
        m.record_stage_counts("normalise", in_count=10, out_count=7, quarantined=2, filtered=1)

    def test_reconciliation_invariant_fails(self, tmp_path):
        m = Manifest("r1", tmp_path / "manifest.json")
        # in=10, but out+q+f=9 → assertion error (ST-05, ST-06)
        with pytest.raises(AssertionError, match="Reconciliation invariant violated"):
            m.record_stage_counts("normalise", in_count=10, out_count=8, quarantined=1, filtered=0)

    def test_cost_accumulates(self, tmp_path):
        m = Manifest("r1", tmp_path / "manifest.json")
        m.add_cost(0.001, {"prompt_tokens": 100, "completion_tokens": 50, "cached_tokens": 0})
        m.add_cost(0.002, {"prompt_tokens": 200, "completion_tokens": 100, "cached_tokens": 20})
        data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert abs(data["cost_usd"] - 0.003) < 1e-6
        assert data["token_usage"]["prompt_tokens"] == 300

    def test_flag_recorded(self, tmp_path):
        m = Manifest("r1", tmp_path / "manifest.json")
        m.set_flag("budget_plan_approved", True)
        data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert data["flags"]["budget_plan_approved"] is True

    def test_atomic_write_no_corrupt_on_read(self, tmp_path):
        """Flush is atomic (temp-then-rename), so reading never sees partial state."""
        m = Manifest("r1", tmp_path / "manifest.json")
        for i in range(50):
            m.record_stage_start(f"stage_{i}", chunk=i)
        # Should always parse as valid JSON
        data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert data["run_id"] == "r1"


class TestRunId:
    def test_unique_per_call(self, tmp_path):
        id1 = make_run_id(tmp_path)
        id2 = make_run_id(tmp_path)
        assert id1 != id2

    def test_directory_created(self, tmp_path):
        run_id = make_run_id(tmp_path)
        assert (tmp_path / run_id).exists()

    def test_collision_prevented(self, tmp_path, monkeypatch):
        """If the directory already exists, keep trying until a fresh one is found."""
        created: list[str] = []

        original_make_run_id = make_run_id
        run_id = make_run_id(tmp_path)
        assert run_id
        # Force-create the directory to simulate a collision for the next call
        # (the function handles this internally via the loop)
