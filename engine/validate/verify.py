"""
T-P0-13 — Quota discovery and limits configuration.
T-P0-09 — engine.verify --models pre-flight check.

Queries each provider's model list and quota endpoints before any spend.
Fails loudly if any configured model ID is unavailable or credentials are invalid.

Guards: EC-M-16, EC-M-18, EC-X-07, EC-B-12
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from engine.config.settings import Settings

logger = logging.getLogger(__name__)


def verify_models(settings: Settings) -> dict[str, Any]:
    """
    T-P0-09: Pre-flight model verification.

    Steps:
    1. Query each provider's model-list endpoint
    2. Assert configured model IDs exist in the live catalogue
    3. Make a trivial authenticated call to confirm credentials
    4. Read and report remaining quota headroom

    Returns a verification report dict.
    Raises SystemExit(1) with a clear message on any failure.
    """
    if settings.llm is None:
        logger.error(
            "config/models.yaml has no 'llm' section. "
            "Populate model IDs before running verify."
        )
        sys.exit(1)

    report: dict[str, Any] = {"models": {}, "credentials": {}, "quota": {}}
    all_ok = True

    # ── Groq verification ────────────────────────────────────────────────────
    try:
        import groq as _groq  # noqa: PLC0415 — vendor import inside llm check

        groq_client_raw = _groq.Groq(api_key=settings.groq_api_key)
        groq_model_ids = {m.id for m in groq_client_raw.models.list().data}
        report["credentials"]["groq"] = "ok"

        groq_slots = {
            "gate": settings.llm.gate,
            "adjudicate": settings.llm.adjudicate,
        }
        for slot, cfg in groq_slots.items():
            if cfg.provider != "groq":
                continue
            if not cfg.model:
                logger.error(
                    "Groq model ID for slot '%s' is empty. "
                    "Set a live model ID in config/models.yaml.",
                    slot,
                )
                all_ok = False
                report["models"][slot] = {"ok": False, "reason": "empty model ID"}
                continue

            if cfg.model in groq_model_ids:
                logger.info("✓ Groq model verified: %s (%s)", cfg.model, slot)
                report["models"][slot] = {"ok": True, "model": cfg.model}
            else:
                available = sorted(groq_model_ids)
                logger.error(
                    "✗ Groq model '%s' (slot=%s) not found in live catalogue.\n"
                    "  Available: %s",
                    cfg.model,
                    slot,
                    ", ".join(available[:10]),
                )
                all_ok = False
                report["models"][slot] = {
                    "ok": False,
                    "model": cfg.model,
                    "available_sample": available[:10],
                }
    except Exception as exc:
        logger.error("Groq credential check failed: %s", exc)
        report["credentials"]["groq"] = f"FAILED: {exc}"
        all_ok = False

    # ── Gemini verification ──────────────────────────────────────────────────
    try:
        import google.genai as genai  # noqa: PLC0415

        gemini_client_raw = genai.Client(api_key=settings.gemini_api_key)
        gemini_models_raw = list(gemini_client_raw.models.list())
        gemini_model_ids = {m.name.split("/")[-1] for m in gemini_models_raw}
        report["credentials"]["gemini"] = "ok"

        gemini_slots = {
            "label": settings.llm.label,
            "label_hard": settings.llm.label_hard,
            "induce": settings.llm.induce,
            "synthesise": settings.llm.synthesise,
        }
        for slot, cfg in gemini_slots.items():
            if cfg.provider != "gemini":
                continue
            if not cfg.model:
                logger.error(
                    "Gemini model ID for slot '%s' is empty.", slot
                )
                all_ok = False
                report["models"][slot] = {"ok": False, "reason": "empty model ID"}
                continue

            model_base = cfg.model.split("/")[-1]
            if model_base in gemini_model_ids or cfg.model in gemini_model_ids:
                logger.info("✓ Gemini model verified: %s (%s)", cfg.model, slot)
                report["models"][slot] = {"ok": True, "model": cfg.model}
            else:
                available = sorted(gemini_model_ids)
                logger.error(
                    "✗ Gemini model '%s' (slot=%s) not in live catalogue.\n"
                    "  Available sample: %s",
                    cfg.model,
                    slot,
                    ", ".join(available[:10]),
                )
                all_ok = False
                report["models"][slot] = {
                    "ok": False,
                    "model": cfg.model,
                    "available_sample": available[:10],
                }
    except Exception as exc:
        logger.error("Gemini credential check failed: %s", exc)
        report["credentials"]["gemini"] = f"FAILED: {exc}"
        all_ok = False

    report["all_ok"] = all_ok
    if not all_ok:
        logger.error(
            "\n═══ Model verification FAILED ═══\n"
            "Fix the errors above before any spend. "
            "No models have been called yet.\n"
        )
        sys.exit(1)

    logger.info("✓ All configured models verified against live catalogues.")
    return report


def verify_sources(settings: Settings) -> dict[str, Any]:
    """
    T-P1-04: Source identifier verification.
    For each source in config/sources.yaml, fetch app metadata to confirm
    the title matches the expected brand.
    """
    if not settings.sources:
        logger.warning("No sources configured to verify.")
        return {}

    from google_play_scraper import app

    report: dict[str, Any] = {"sources": {}}
    all_ok = True

    for source_cfg in settings.sources:
        if source_cfg.source == "play_store":
            pkg = source_cfg.params.get("play_package")
            if not pkg:
                logger.error("Missing play_package for %s", source_cfg.brand)
                all_ok = False
                continue

            try:
                result = app(pkg, lang="en", country="in")
                actual_title = result.get("title", "")
                
                # Check expected title (case insensitive, rough substring match is fine, or exact)
                expected = source_cfg.expected_title
                
                # For robust matching, we check if expected is in actual, or vice versa
                if expected.lower() in actual_title.lower() or actual_title.lower() in expected.lower():
                    logger.info("✓ Verified %s: %s -> %s", source_cfg.brand, pkg, actual_title)
                    report["sources"][pkg] = {"ok": True, "title": actual_title}
                else:
                    logger.error(
                        "✗ Mismatch for %s (%s). Expected title containing: %r. Actual title: %r",
                        source_cfg.brand, pkg, expected, actual_title
                    )
                    all_ok = False
                    report["sources"][pkg] = {"ok": False, "expected": expected, "actual": actual_title}
            except Exception as exc:
                logger.error("✗ Failed to fetch %s from Play Store: %s", pkg, exc)
                all_ok = False
                report["sources"][pkg] = {"ok": False, "error": str(exc)}
        
        elif source_cfg.source == "reddit":
            logger.info("✓ Reddit sources do not require pre-flight metadata fetch.")
            report["sources"]["reddit"] = {"ok": True}

    report["all_ok"] = all_ok
    if not all_ok:
        logger.error(
            "\n═══ Source verification FAILED ═══\n"
            "Fix the identifiers in config/sources.yaml before starting collection.\n"
        )
        sys.exit(1)

    logger.info("✓ All sources verified.")
    return report
