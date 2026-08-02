import argparse
import json
import logging
import re
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
DASHBOARD_DATA_DIR = REPO_ROOT / "dashboard" / "public" / "data"

# Common PII Regex Patterns for leak check
EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_PATTERN = re.compile(r"\+?\d{10,14}")
AUTHOR_HASH_PATTERN = re.compile(r'"author_hash"\s*:\s*')
URL_PATTERN = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

def fail_closed(message: str) -> None:
    """Hard abort on leak detection."""
    logger.error(f"LEAK CHECK FAILED: {message}")
    sys.exit(1)

def run_leak_check(json_string: str, context: str) -> None:
    """Fails closed if the payload contains banned patterns."""
    if EMAIL_PATTERN.search(json_string):
        fail_closed(f"Email pattern detected in {context}")
    if PHONE_PATTERN.search(json_string):
        fail_closed(f"Phone pattern detected in {context}")
    if AUTHOR_HASH_PATTERN.search(json_string):
        fail_closed(f"author_hash key detected in {context}")
    if URL_PATTERN.search(json_string):
        fail_closed(f"URL pattern detected in {context}")
    logger.info(f"Leak check passed for {context}")

def write_sanitised_json(data: dict, filename: str) -> None:
    """Validates the output json string against leak checks and writes it to disk."""
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_string = json.dumps(data, indent=2)
    
    # 6. Run leak check
    run_leak_check(json_string, filename)
    
    out_path = DASHBOARD_DATA_DIR / filename
    out_path.write_text(json_string, encoding="utf-8")
    logger.info(f"Wrote {out_path}")

def export_themes(run_id: str) -> None:
    """Sanitise themes data to barriers.json"""
    in_file = DATA_DIR / "themes" / run_id / "themes.json"
    if not in_file.exists():
        logger.warning(f"No themes found at {in_file}")
        return
        
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sanitised_themes = []
    # 5. Enforce an allow-list schema
    for theme in data.get("themes", []):
        safe_theme = {
            "theme_id": theme.get("theme_id"),
            "name": theme.get("name"),
            "description": theme.get("description"),
            "frequency": theme.get("frequency", 0),
            "exemplar_quotes": theme.get("exemplar_quotes", [])
        }
        sanitised_themes.append(safe_theme)
        
    write_sanitised_json({"themes": sanitised_themes}, "barriers.json")

def export_insights(run_id: str) -> None:
    """Sanitise insights data to insights.json"""
    in_file = DATA_DIR / "insights" / run_id / "insights.json"
    if not in_file.exists():
        logger.warning(f"No insights found at {in_file}")
        return
        
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sanitised_insights = []
    # 5. Enforce an allow-list schema
    for ins in data.get("insights", []):
        safe_insight = {
            "research_question_id": ins.get("research_question_id"),
            "claim": ins.get("claim"),
            "confidence": ins.get("confidence"),
            "implication": ins.get("implication"),
            "segment": ins.get("segment", "Unknown"),
            "brand_attribution": ins.get("brand_attribution", "Applies to both"),
            "bias_direction": ins.get("bias_direction", "None"),
            "barrier_classification": ins.get("barrier_classification", "N/A"),
            "contradicting_evidence": ins.get("contradicting_evidence", "None"),
        }
        sanitised_insights.append(safe_insight)
        
    write_sanitised_json({"insights": sanitised_insights}, "insights.json")

def export_validation(run_id: str) -> None:
    """Sanitise validation results to validation.json"""
    in_file = DATA_DIR / "validation" / run_id / "results.json"
    if not in_file.exists():
        logger.warning(f"No validation results found at {in_file}")
        return
        
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Validation data is generally safe metadata, but we'll schema restrict anyway
    safe_val = {
        "run_id": data.get("run_id"),
        "groundedness_pass_rate": data.get("groundedness", {}).get("pass_rate", 0),
        "coverage_percentage": data.get("coverage", {}).get("coverage_percentage", 0),
        "triangulation_downgraded_themes": data.get("triangulation", {}).get("downgraded_themes", []),
        "biases": data.get("bias", {}).get("skews", {}),
        "reliability_kappa": data.get("reliability", {}).get("cohens_kappa", {})
    }
    
    write_sanitised_json(safe_val, "validation.json")

def main() -> None:
    parser = argparse.ArgumentParser(description="Export sanitised JSON for Vercel")
    parser.add_argument("--run-id", type=str, required=True, help="The run_id to export")
    args = parser.parse_args()
    
    logger.info(f"Exporting run: {args.run_id}")
    export_themes(args.run_id)
    export_insights(args.run_id)
    export_validation(args.run_id)
    logger.info("Export complete.")

if __name__ == "__main__":
    main()
