import json
from pathlib import Path
from typing import Dict, Any

def generate_mock_gold_set(validation_dir: Path) -> None:
    """Generates a mock gold set for testing the Validation Harness."""
    gold_set_path = validation_dir / "mock_gold_set.json"
    gold_set_path.parent.mkdir(parents=True, exist_ok=True)
    
    mock_data = {
        "verbatims": [
            {
                "verbatim_id": f"mock_verbatim_{i}",
                "gold_labels": ["Pricing", "Quality"],
                "model_labels": ["Pricing", "Quality"] if i % 10 != 0 else ["Pricing"]
            }
            for i in range(200)
        ]
    }
    
    with open(gold_set_path, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)

def generate_mock_stability_run(validation_dir: Path) -> None:
    """Generates a mock stability run result."""
    stability_path = validation_dir / "mock_stability.json"
    stability_path.parent.mkdir(parents=True, exist_ok=True)
    
    mock_data = {
        "overlap_score": 0.92
    }
    
    with open(stability_path, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)

def generate_mock_cross_provider_run(validation_dir: Path) -> None:
    """Generates a mock cross-provider run result."""
    cross_path = validation_dir / "mock_cross_provider.json"
    cross_path.parent.mkdir(parents=True, exist_ok=True)
    
    mock_data = {
        "groq_gemini_kappa": 0.85,
        "groq_human_kappa": 0.82,
        "gemini_human_kappa": 0.87
    }
    
    with open(cross_path, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)
