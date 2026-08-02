"""
CLI entry point for the engine.

All commands run through here. Every command calls configure_logging() before
any other work, wires get_settings(), and validates config up front (EC-X-07).

PYTHONUTF8=1 is set in the Makefile run targets (ST-01).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Repo root (for data/ and runs/ directories)
# ─────────────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).parent.parent

logger = logging.getLogger(__name__)


def _get_run_id(runs_dir: Path) -> str:
    from engine.store.manifest import make_run_id
    return make_run_id(runs_dir)


def cmd_verify(args: argparse.Namespace) -> None:
    """engine.verify — pre-flight checks (T-P0-09)."""
    from engine.config.settings import get_settings
    from engine.store.manifest import configure_logging, make_run_id

    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)

    settings = get_settings()

    if args.target in ("models", "all"):
        from engine.validate.verify import verify_models

        logger.info("Running model verification (T-P0-09)...")
        report = verify_models(settings)
        print(json.dumps(report, indent=2))

    if args.target in ("sources", "all"):
        from engine.validate.verify import verify_sources

        logger.info("Running source verification (T-P1-04)...")
        report_sources = verify_sources(settings)
        print(json.dumps(report_sources, indent=2))

    logger.info("Verification complete.")


def cmd_spike(args: argparse.Namespace) -> None:
    """engine.spike — run T-P0-11 provider spike."""
    from engine.config.settings import get_settings
    from engine.llm.gemini_client import GeminiClient
    from engine.llm.groq_client import GroqClient
    from engine.label.spike import DEFAULT_SPIKE_VERBATIMS, run_spike
    from engine.store.manifest import configure_logging, make_run_id

    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)

    settings = get_settings()
    if settings.llm is None:
        logger.error("No LLM config — populate config/models.yaml first.")
        sys.exit(1)

    groq = GroqClient(
        api_key=settings.groq_api_key,
        model=settings.llm.gate.model,
        rpm=settings.llm.gate.rpm,
        tpm=settings.llm.gate.tpm,
    )
    gemini = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.llm.label.model,
        rpm=settings.llm.label.rpm,
        tpm=settings.llm.label.tpm,
    )

    output = _REPO_ROOT / "data" / "runs" / run_id / "spike_report.json"
    run_spike(groq, gemini, DEFAULT_SPIKE_VERBATIMS, output_path=output)
    print(f"\nSpike report written to: {output}")
    print("Next: update ARCH §16 with measured tokens/doc values.")


def cmd_collect(args: argparse.Namespace) -> None:
    """Execute a collection run."""
    from engine.config.settings import get_settings
    from engine.store.manifest import configure_logging, make_run_id
    from engine.collection.runner import run_collection

    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)

    logger.info("Starting collection...")
    settings = get_settings()

    run_collection(
        settings=settings,
        data_dir=_REPO_ROOT / "data",
        target_source=args.source if args.source != "all" else None,
        acknowledge_low=args.acknowledge_low,
    )

    logger.info("Collection complete.")

def cmd_induce(args: argparse.Namespace) -> None:
    """Run codebook induction phase (T-P3)."""
    from engine.config.settings import get_settings
    from engine.store.manifest import configure_logging
    
    # Let runner create its own run_id if it wants, but we'll init logging anyway
    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    from engine.store.manifest import make_run_id
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)
    
    settings = get_settings()
    settings.validate_all()
    data_dir = _REPO_ROOT / "data"
    
    from engine.induce.runner import run_phase3
    run_phase3(settings, data_dir, args.snapshot)


def cmd_label(args: argparse.Namespace) -> None:
    """Run Phase 4 labelling (T-P4)."""
    from engine.config.settings import get_settings
    from engine.store.manifest import configure_logging, make_run_id
    
    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)
    
    settings = get_settings()
    settings.validate_all()
    data_dir = _REPO_ROOT / "data"
    
    from engine.label.runner import run_phase4
    run_phase4(settings, data_dir, args.snapshot)


def cmd_cluster(args: argparse.Namespace) -> None:
    """Run Phase 5 clustering and semantic merging."""
    from engine.config.settings import get_settings
    from engine.store.manifest import configure_logging, make_run_id
    
    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)
    
    settings = get_settings()
    data_dir = _REPO_ROOT / "data"
    
    import json
    from engine.label.schema import Label
    from engine.cluster.aggregator import aggregate_themes
    from engine.cluster.merger import semantic_merge
    from engine.llm.groq_client import GroqClient
    
    # 1. Load latest labels (or from specific run_id if provided, for simplicity we assume latest)
    labels_dir = data_dir / "labels"
    if not labels_dir.exists():
        logger.error("No labels found. Run phase 4 first.")
        return
        
    latest_run = sorted([d for d in labels_dir.iterdir() if d.is_dir()])[-1]
    labels_file = latest_run / "labels.jsonl"
    
    logger.info(f"Loading labels from {labels_file}")
    labels = []
    with open(labels_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                labels.append(Label.model_validate_json(line))
                
    # 2. Aggregate Themes
    theme_collection = aggregate_themes(labels, data_dir)
    
    # 3. Semantic Merge
    groq_model = "llama-3.1-8b-instant"
    groq_client = GroqClient(
        api_key=settings.groq_api_key,
        model=groq_model,
        rpm=30,
        tpm=6000
    )
    
    merged_themes = semantic_merge(
        themes=theme_collection,
        groq_client=groq_client,
        model_id=groq_model,
        log_dir=runs_dir / run_id
    )
    
    # 4. Save
    out_dir = data_dir / "themes" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "themes.json", "w", encoding="utf-8") as f:
        f.write(merged_themes.model_dump_json(indent=2))
        
    logger.info(f"Phase 5 clustering complete. Saved to {out_dir / 'themes.json'}")

def cmd_synthesise(args: argparse.Namespace) -> None:
    """Run Phase 5 insight synthesis."""
    from engine.config.settings import get_settings
    from engine.store.manifest import configure_logging, make_run_id
    
    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)
    
    settings = get_settings()
    data_dir = _REPO_ROOT / "data"
    
    from engine.cluster.schema import ThemeCollection
    from engine.synthesise.synthesiser import synthesize_insights
    from engine.llm.gemini_client import GeminiClient
    
    themes_dir = data_dir / "themes"
    if not themes_dir.exists():
        logger.error("No themes found. Run cluster command first.")
        return
        
    latest_run = sorted([d for d in themes_dir.iterdir() if d.is_dir()])[-1]
    themes_file = latest_run / "themes.json"
    
    logger.info(f"Loading themes from {themes_file}")
    with open(themes_file, "r", encoding="utf-8") as f:
        themes = ThemeCollection.model_validate_json(f.read())
        
    gemini_model = "gemini-2.0-flash"
    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=gemini_model,
        rpm=15,
        tpm=32000
    )
    
    insights = synthesize_insights(themes, gemini_client, gemini_model)
    
    out_dir = data_dir / "insights" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "insights.json", "w", encoding="utf-8") as f:
        f.write(insights.model_dump_json(indent=2))
        
    logger.info(f"Phase 5 synthesis complete. Saved to {out_dir / 'insights.json'}")

def cmd_validate(args: argparse.Namespace) -> None:
    """Run Phase 6 Validation Harness (T-P6)."""
    from engine.store.manifest import configure_logging, make_run_id
    from engine.validate.harness import ValidationHarness
    
    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)
    
    # In a real run, we might want to validate a specific run_id.
    # For now, we just pass the run_id we generated.
    logger.info("Starting Phase 6 Validation Harness...")
    
    harness = ValidationHarness(run_id=run_id, data_dir=str(_REPO_ROOT / "data"))
    output = harness.run_all()
    
    logger.info(f"Validation complete. Results saved to {harness.validation_dir / 'results.json'}")

def cmd_report(args: argparse.Namespace) -> None:
    """Run Phase 7 Reports and Deliverables (T-P7)."""
    from engine.store.manifest import configure_logging, make_run_id
    from engine.report.generator import run_report_generation
    
    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)
    
    logger.info("Starting Phase 7 Report Generation...")
    
    # Normally we would use the specific run_id we want to report on.
    # We will search for the latest validation results for this demo.
    validation_dir = _REPO_ROOT / "data" / "validation"
    if not validation_dir.exists():
        logger.error("No validation data found. Run validate first.")
        return
        
    latest_run = sorted([d for d in validation_dir.iterdir() if d.is_dir()])[-1]
    
    run_report_generation(run_id=latest_run.name, data_dir=str(_REPO_ROOT / "data"))

def cmd_plan(args: argparse.Namespace) -> None:
    """engine.plan — run T-P0-14 token budget planner."""
    from engine.config.settings import get_settings
    from engine.store.budget import (
        BudgetPlan,
        ProviderLimits,
        SpikeMeasurement,
        compute_budget_plan,
    )
    from engine.store.manifest import configure_logging, make_run_id

    runs_dir = _REPO_ROOT / "data" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    configure_logging(run_id=run_id)

    settings = get_settings()
    if settings.llm is None:
        logger.error("No LLM config.")
        sys.exit(1)

    gate = settings.llm.gate
    label = settings.llm.label

    gate_limits = ProviderLimits(
        provider=gate.provider,
        model=gate.model,
        tpd=gate.tpd,
        tpm=gate.tpm,
        rpm=gate.rpm,
    )
    label_limits = ProviderLimits(
        provider=label.provider,
        model=label.model,
        tpd=label.tpd,
        tpm=label.tpm,
        rpm=label.rpm,
    )

    # These must be filled from the spike report (T-P0-11)
    gate_spike = SpikeMeasurement(
        avg_prompt_tokens_per_doc=args.gate_prompt or 0,
        avg_completion_tokens_per_doc=args.gate_completion or 0,
    )
    label_spike = SpikeMeasurement(
        avg_prompt_tokens_per_doc=args.label_prompt or 0,
        avg_completion_tokens_per_doc=args.label_completion or 0,
        avg_cached_tokens_per_doc=args.label_cached or 0,
    )

    plan = compute_budget_plan(
        gate_limits=gate_limits,
        label_limits=label_limits,
        gate_spike=gate_spike,
        label_spike=label_spike,
        corpus_size=args.corpus_size,
        gate_pass_rate=args.gate_pass_rate,
        wall_clock_window_days=args.window_days,
        cost_ceiling_usd=settings.cost.ceiling_usd,
    )
    print(plan.summary())
    print("\nFull plan JSON:")
    print(json.dumps(plan.to_dict(), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m engine.cli",
        description="Blinkit Review Analyser — AI-Powered Discovery Engine",
    )
    sub = parser.add_subparsers(dest="command")

    # verify
    verify_p = sub.add_parser("verify", help="Pre-flight checks (T-P0-09)")
    verify_p.add_argument(
        "--target",
        choices=["models", "sources", "all"],
        default="all",
        help="What to verify",
    )

    # spike
    sub.add_parser("spike", help="Run T-P0-11 provider spike (20 verbatims × 2 providers)")

    # plan
    parser_plan = sub.add_parser("plan", help="Run token budget planner")
    parser_plan.add_argument("--corpus-size", type=int, required=True)
    parser_plan.add_argument("--gate-pass-rate", type=float, default=0.55)
    parser_plan.add_argument("--window-days", type=int, default=7)
    parser_plan.add_argument("--gate-prompt", type=float, default=None,
                        help="Measured avg prompt tokens/doc for gate (from spike)")
    parser_plan.add_argument("--gate-completion", type=float, default=None)
    parser_plan.add_argument("--label-prompt", type=float, default=None)
    parser_plan.add_argument("--label-completion", type=float, default=None)
    parser_plan.add_argument("--label-cached", type=float, default=0.0)

    # collect
    parser_collect = sub.add_parser("collect", help="Execute collection run")
    parser_collect.add_argument(
        "--source",
        type=str,
        default="all",
        help="Specific source to run (e.g. play_store), or all",
    )
    parser_collect.add_argument(
        "--acknowledge-low",
        action="store_true",
        help="Proceed even if minimum expected count is not met (EC-C-10).",
    )

    # induce
    parser_induce = sub.add_parser("induce", help="Run Phase 3 codebook induction")
    parser_induce.add_argument(
        "--snapshot",
        type=str,
        default="",
        help="Target snapshot ID (optional, defaults to current latest)",
    )

    # label
    parser_label = sub.add_parser("label", help="Run Phase 4 labelling")
    parser_label.add_argument(
        "--snapshot",
        type=str,
        default="",
        help="Target snapshot ID (optional)",
    )
    
    # cluster
    parser_cluster = sub.add_parser("cluster", help="Run Phase 5 theme clustering and merging")
    
    # synthesise
    parser_synthesise = sub.add_parser("synthesise", help="Run Phase 5 insight synthesis")

    # validate
    parser_validate = sub.add_parser("validate", help="Run Phase 6 validation harness")
    
    # report
    parser_report = sub.add_parser("report", help="Run Phase 7 report generation")

    return parser


def main() -> None:
    # Ensure UTF-8 mode (ST-01)
    if os.environ.get("PYTHONUTF8") != "1":
        os.environ["PYTHONUTF8"] = "1"

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "verify": cmd_verify,
        "spike": cmd_spike,
        "plan": cmd_plan,
        "collect": cmd_collect,
        "induce": cmd_induce,
        "label": cmd_label,
        "cluster": cmd_cluster,
        "synthesise": cmd_synthesise,
        "validate": cmd_validate,
        "report": cmd_report,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
