import pytest
import json
from pathlib import Path

from engine.validate.schema import (
    GroundednessResult,
    CoverageResult,
    TriangulationResult,
    BiasReport,
    QuotaSamplingBias,
    ReliabilityResult
)
from engine.validate.harness import ValidationHarness

def test_groundedness_mock():
    harness = ValidationHarness(run_id="test_run", data_dir="data")
    result = harness._check_groundedness()
    assert isinstance(result, GroundednessResult)
    assert result.pass_rate == 1.0

def test_coverage_mock():
    harness = ValidationHarness(run_id="test_run", data_dir="data")
    result = harness._check_coverage()
    assert isinstance(result, CoverageResult)
    assert result.processed_verbatims_count == 1000
    assert result.coverage_percentage == 85.0

def test_triangulation_mock():
    harness = ValidationHarness(run_id="test_run", data_dir="data")
    result = harness._check_triangulation()
    assert isinstance(result, TriangulationResult)
    assert "theme_2" in result.downgraded_themes

def test_bias_characterisation_mock():
    harness = ValidationHarness(run_id="test_run", data_dir="data")
    result = harness._characterise_bias()
    assert isinstance(result, BiasReport)
    assert "platform_extremes" in result.skews

def test_quota_sampling_bias_mock():
    harness = ValidationHarness(run_id="test_run", data_dir="data")
    result = harness._check_quota_sampling()
    assert isinstance(result, QuotaSamplingBias)
    assert "truncation" in result.bias_directions

def test_reliability_mock(tmp_path):
    harness = ValidationHarness(run_id="test_run", data_dir=str(tmp_path))
    result = harness._check_reliability()
    assert isinstance(result, ReliabilityResult)
    assert result.cohens_kappa["barrier_identification"] == 0.88
    # Ensure mock file was generated
    mock_file = tmp_path / "validation" / "test_run" / "mock_gold_set.json"
    assert mock_file.exists()

def test_harness_run_all(tmp_path):
    harness = ValidationHarness(run_id="test_run", data_dir=str(tmp_path))
    output = harness.run_all()
    
    assert output.run_id == "test_run"
    assert output.snapshot_id == "test_run_snapshot"
    assert output.stability_overlap_score == 0.92
    assert output.cross_provider_kappa["groq_gemini_kappa"] == 0.85
    
    # Check if results were saved
    results_file = tmp_path / "validation" / "test_run" / "results.json"
    assert results_file.exists()
    
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["run_id"] == "test_run"
    assert "groundedness" in data
    assert "coverage" in data
