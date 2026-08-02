import pytest
import json
from pathlib import Path
from engine.report.generator import run_report_generation

def test_report_generation_with_empty_data(tmp_path):
    # Set up mock data directory
    data_dir = tmp_path / "data"
    run_id = "test_run"
    
    # Run generator (should handle missing files gracefully)
    run_report_generation(run_id, data_dir=str(data_dir))
    
    # Check outputs
    out_dir = data_dir / "deliverables" / run_id
    assert out_dir.exists()
    
    assert (out_dir / "deliverable_1_engine_docs.md").exists()
    assert (out_dir / "deliverable_3_codebook.md").exists()
    assert (out_dir / "deliverable_4_validation.md").exists()
    assert (out_dir / "deliverable_5_insight.md").exists()
    assert (out_dir / "deliverable_6_segment.md").exists()
    assert (out_dir / "appendix_parking_lot.md").exists()

def test_report_generation_with_solution_language(tmp_path):
    # Test that parking lot correctly identifies solution language
    data_dir = tmp_path / "data"
    run_id = "test_run"
    
    insights_dir = data_dir / "insights" / run_id
    insights_dir.mkdir(parents=True)
    
    mock_insights = {
        "insights": [
            {
                "research_question_id": "RQ1",
                "claim": "Price is too high",
                "confidence": "high",
                "implication": "We should build a discount feature."
            },
            {
                "research_question_id": "RQ2",
                "claim": "App is slow",
                "confidence": "high",
                "implication": "Users are abandoning the app."
            }
        ]
    }
    
    with open(insights_dir / "insights.json", "w") as f:
        json.dump(mock_insights, f)
        
    run_report_generation(run_id, data_dir=str(data_dir))
    
    out_dir = data_dir / "deliverables" / run_id
    
    # Check insight report hides solution
    insight_content = (out_dir / "deliverable_5_insight.md").read_text()
    assert "We should build a discount feature" not in insight_content
    assert "[Solution suggestion moved to Parking Lot]" in insight_content
    assert "Users are abandoning the app" in insight_content
    
    # Check parking lot contains solution
    parking_content = (out_dir / "appendix_parking_lot.md").read_text()
    assert "We should build a discount feature" in parking_content
