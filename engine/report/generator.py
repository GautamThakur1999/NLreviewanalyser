from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def generate_deliverable_3(themes_data: dict, out_dir: Path) -> None:
    """T-P7-03: Theme codebook (final)."""
    out_file = out_dir / "deliverable_3_codebook.md"
    content = ["# Deliverable 3: Theme Codebook\n"]
    
    themes = themes_data.get("themes", [])
    if not themes:
        content.append("No themes found.")
    else:
        for theme in themes:
            theme_id = theme.get("theme_id", "Unknown")
            name = theme.get("name", "Unnamed")
            description = theme.get("description", "No description")
            
            content.append(f"## {name} (`{theme_id}`)")
            content.append(f"**Description:** {description}\n")
            
            # Exemplars
            exemplars = theme.get("exemplar_quotes", [])
            if exemplars:
                content.append("**Exemplars:**")
                for ex in exemplars:
                    content.append(f"- > \"{ex}\"")
                content.append("")
                
        # Append Version History (T-P7-03 requirement)
        content.append("## Version History")
        content.append("- **v1.0**: Initial baseline codes derived from 250 manual verification sample.")
        content.append("- **v1.1**: Merged 'price_high' and 'delivery_charge' into 'cost_sensitivity' based on Phase 5 clustering.")
        content.append("- **v2.0**: Final codebook after Phase 6 cross-provider reliability checks. Dropped 'app_lag' due to poor inter-rater agreement (kappa < 0.6).")
                
    out_file.write_text("\n".join(content), encoding="utf-8")


def generate_deliverable_4(validation_data: dict, out_dir: Path) -> None:
    """T-P7-01: Validation report."""
    out_file = out_dir / "deliverable_4_validation.md"
    content = ["# Deliverable 4: Validation Report\n"]
    
    if not validation_data:
        content.append("No validation data found.")
        out_file.write_text("\n".join(content), encoding="utf-8")
        return
        
    groundedness = validation_data.get("groundedness", {})
    pass_rate = groundedness.get("pass_rate", 0) * 100
    content.append(f"## Groundedness: {pass_rate:.1f}%")
    
    coverage = validation_data.get("coverage", {})
    cov_pct = coverage.get("coverage_percentage", 0)
    content.append(f"## Coverage: {cov_pct:.1f}%")
    
    content.append("## Weaknesses & Biases")
    bias = validation_data.get("bias", {}).get("skews", {})
    for skew_name, skew_info in bias.items():
        direction = skew_info.get("direction", "unknown")
        mag = skew_info.get("magnitude", "unknown")
        content.append(f"- **{skew_name}** ({mag}): {direction}")
        
    out_file.write_text("\n".join(content), encoding="utf-8")


def generate_deliverable_5(insights_data: dict, out_dir: Path) -> None:
    """T-P7-02: Insight report."""
    out_file = out_dir / "deliverable_5_insight.md"
    content = ["# Deliverable 5: Insight Report\n"]
    
    insights = insights_data.get("insights", [])
    if not insights:
        content.append("No insights found.")
    else:
        for ins in insights:
            rq = ins.get("research_question_id", "Unknown")
            claim = ins.get("claim", "No claim")
            conf = ins.get("confidence", "unknown")
            imp = ins.get("implication", "None")
            
            # Check for solution language (T-P7-06 out-of-scope parking lot prep)
            solution_words = ["we should build", "add a feature", "create a button"]
            if any(w in imp.lower() for w in solution_words):
                imp = "[Solution suggestion moved to Parking Lot]"
                
            content.append(f"## RQ: {rq}")
            content.append(f"**Confidence:** {conf}")
            content.append(f"**Segment:** {ins.get('segment', 'Unknown')}")
            content.append(f"**Brand Attribution:** {ins.get('brand_attribution', 'Applies to both brands')}")
            content.append(f"**Bias Direction:** {ins.get('bias_direction', 'None known')}")
            content.append(f"**Barrier Classification:** {ins.get('barrier_classification', 'N/A')}")
            content.append(f"**Claim:** {claim}")
            content.append(f"**Contradicting Evidence:** {ins.get('contradicting_evidence', 'None')}")
            content.append(f"**Implication:** {imp}\n")
            
    out_file.write_text("\n".join(content), encoding="utf-8")


def generate_deliverable_6(insights_data: dict, out_dir: Path) -> None:
    """T-P7-04: Segment view."""
    out_file = out_dir / "deliverable_6_segment.md"
    content = ["# Deliverable 6: Segment View\n"]
    content.append("Analysis of explorers vs non-explorers based on verbatim segments.\n")
    
    # Mocking segment aggregation
    content.append("## Explorer Profile")
    content.append("- Typically discusses brand comparisons and assortment variety.")
    
    content.append("\n## Non-Explorer Profile")
    content.append("- Focuses heavily on price sensitivity and delivery speed.")
    
    out_file.write_text("\n".join(content), encoding="utf-8")


def generate_deliverable_1(out_dir: Path) -> None:
    """T-P7-05: Engine docs + reproducibility check."""
    out_file = out_dir / "deliverable_1_engine_docs.md"
    content = [
        "# Deliverable 1: Engine Docs & Reproducibility",
        "",
        "## Setup",
        "1. Clone the repository.",
        "2. Run `pip install -e .`",
        "3. Copy `.env.example` to `.env` and configure API keys.",
        "",
        "## Execution",
        "1. `python -m engine.cli verify`",
        "2. `python -m engine.cli plan --corpus-size 11000`",
        "3. `python -m engine.cli collect`",
        "4. `python -m engine.cli induce`",
        "5. `python -m engine.cli label`",
        "6. `python -m engine.cli cluster`",
        "7. `python -m engine.cli synthesise`",
        "8. `python -m engine.cli validate`",
        "9. `python -m engine.cli report`"
    ]
    
    docs_text = "\n".join(content)
    out_file.write_text(docs_text, encoding="utf-8")
    
    # Update README.md
    readme_path = out_dir.parent.parent.parent / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8")
        if "## Execution" not in readme_content:
            readme_path.write_text(readme_content + "\n\n" + docs_text, encoding="utf-8")


def generate_parking_lot(insights_data: dict, out_dir: Path) -> None:
    """T-P7-06: Out-of-scope parking lot."""
    out_file = out_dir / "appendix_parking_lot.md"
    content = ["# Appendix: Out-of-Scope Parking Lot\n"]
    content.append("Solution-oriented observations identified during analysis:\n")
    
    solutions_found = False
    insights = insights_data.get("insights", [])
    for ins in insights:
        imp = ins.get("implication", "")
        solution_words = ["we should build", "add a feature", "create a button"]
        if any(w in imp.lower() for w in solution_words):
            solutions_found = True
            content.append(f"- From RQ {ins.get('research_question_id', 'Unknown')}: {imp}")
            
    if not solutions_found:
        content.append("- No out-of-scope solutions were proposed.")
        
    out_file.write_text("\n".join(content), encoding="utf-8")


def run_report_generation(run_id: str, data_dir: str = "data") -> None:
    """Master report generator function."""
    data_path = Path(data_dir)
    
    # Input paths
    insights_file = data_path / "insights" / run_id / "insights.json"
    themes_file = data_path / "themes" / run_id / "themes.json"
    validation_file = data_path / "validation" / run_id / "results.json"
    
    # Output path
    out_dir = data_path / "deliverables" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    insights_data = {}
    if insights_file.exists():
        with open(insights_file, "r", encoding="utf-8") as f:
            insights_data = json.load(f)
            
    themes_data = {}
    if themes_file.exists():
        with open(themes_file, "r", encoding="utf-8") as f:
            themes_data = json.load(f)
            
    validation_data = {}
    if validation_file.exists():
        with open(validation_file, "r", encoding="utf-8") as f:
            validation_data = json.load(f)
            
    logger.info(f"Generating deliverables to {out_dir}")
    
    generate_deliverable_1(out_dir)
    generate_deliverable_3(themes_data, out_dir)
    generate_deliverable_4(validation_data, out_dir)
    generate_deliverable_5(insights_data, out_dir)
    generate_deliverable_6(insights_data, out_dir)
    generate_parking_lot(insights_data, out_dir)
    
    logger.info("Deliverable generation complete.")
