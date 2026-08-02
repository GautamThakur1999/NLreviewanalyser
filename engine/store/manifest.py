"""
T-P0-12 — Structured logging, run_id, and incremental manifest writer.

Provides:
- JSON-lines logging with run_id / stage / counts on every record (ST-14)
- Collision-safe run_id (timestamp + random suffix)
- Manifest object that flushes to disk after every chunk/stage (ST-10)
- Log redaction so secrets never reach the log (ST-12)

Guards: EC-ST-04, EC-ST-06; ST-10, ST-14
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Secret redaction (ST-12)
# ─────────────────────────────────────────────────────────────────────────────

_SECRET_PATTERN = re.compile(
    r"((?:api[_-]?key|token|secret|password|salt|auth)[=:]\s*)[^\s,\"\']{6,}",
    re.IGNORECASE,
)


def _redact(message: str) -> str:
    """Replace secret-looking values with [REDACTED]."""
    return _SECRET_PATTERN.sub(r"\1[REDACTED]", message)


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.msg = _redact(str(record.msg))
        if record.args:
            record.args = tuple(_redact(str(a)) for a in record.args)
        return True


# ─────────────────────────────────────────────────────────────────────────────
# JSON-lines log handler
# ─────────────────────────────────────────────────────────────────────────────


class JsonLinesHandler(logging.StreamHandler):
    """Emits one JSON object per log record (ST-14)."""

    def __init__(self, run_id: str, stream: Any = None) -> None:
        super().__init__(stream)
        self._run_id = run_id

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "run_id": self._run_id,
            "level": record.levelname,
            "logger": record.name,
            "stage": getattr(record, "stage", None),
            "msg": self.format(record),
        }
        # Add any extra counts fields
        for key in ("in_count", "out_count", "quarantined", "filtered"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        try:
            self.stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.stream.flush()
        except Exception:  # noqa: BLE001
            self.handleError(record)


def configure_logging(run_id: str, log_path: Path | None = None, level: int = logging.INFO) -> None:
    """
    Set up structured JSON-lines logging for a run.

    Call once at CLI entry (engine.cli). All subsequent loggers inherit the
    run_id. Secrets are redacted before any log line is written (ST-12).
    """
    root = logging.getLogger()
    root.setLevel(level)
    root.addFilter(RedactingFilter())

    # Console handler (JSON lines)
    console = JsonLinesHandler(run_id=run_id)
    console.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(console)

    # Optional file handler
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = JsonLinesHandler(run_id=run_id, stream=open(log_path, "a", encoding="utf-8"))  # noqa: WPS515 SIM115
        fh.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(fh)


# ─────────────────────────────────────────────────────────────────────────────
# run_id generation
# ─────────────────────────────────────────────────────────────────────────────


def make_run_id(runs_dir: Path) -> str:
    """
    Generate a collision-safe run_id and assert its directory doesn't exist.

    Format: YYYYMMDD-HHMMSS-<6-char random suffix>
    """
    for _ in range(10):
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
        suffix = uuid.uuid4().hex[:6]
        run_id = f"{ts}-{suffix}"
        run_dir = runs_dir / run_id
        if not run_dir.exists():
            run_dir.mkdir(parents=True, exist_ok=False)
            return run_id
    raise RuntimeError(
        f"Could not generate a unique run_id in {runs_dir} after 10 attempts. "
        "Check for stale directories."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Manifest writer (incremental — flushed per chunk, not only at success)
# ─────────────────────────────────────────────────────────────────────────────


class Manifest:
    """
    Incrementally-written run manifest.

    Flushed to disk after every stage boundary and every chunk (ST-10).
    A mid-run kill must leave a valid, readable partial manifest (EC-ST-06).
    """

    def __init__(self, run_id: str, manifest_path: Path) -> None:
        self._run_id = run_id
        self._path = manifest_path
        self._data: dict[str, Any] = {
            "run_id": run_id,
            "started_at": datetime.now(tz=timezone.utc).isoformat(),
            "status": "running",
            "stages": {},
            "cost_usd": 0.0,
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cached_tokens": 0,
            },
            "safety_blocks": {},
            "flags": {},
        }
        self._flush()

    def record_stage_start(self, stage: str, **extra: Any) -> None:
        self._data["stages"].setdefault(stage, {})
        self._data["stages"][stage]["started_at"] = datetime.now(tz=timezone.utc).isoformat()
        self._data["stages"][stage].update(extra)
        self._flush()

    def record_stage_counts(
        self,
        stage: str,
        in_count: int,
        out_count: int,
        quarantined: int = 0,
        filtered: int = 0,
        **extra: Any,
    ) -> None:
        """
        Record and assert the reconciliation invariant:
        in_count == out_count + quarantined + filtered  (ST-05)
        """
        total = out_count + quarantined + filtered
        assert total == in_count, (
            f"Reconciliation invariant violated in stage '{stage}': "
            f"in={in_count} but out+quarantined+filtered={total} "
            f"({out_count}+{quarantined}+{filtered}). "
            "Nothing should be silently dropped (ST-06)."
        )
        self._data["stages"].setdefault(stage, {})
        self._data["stages"][stage].update(
            {
                "in_count": in_count,
                "out_count": out_count,
                "quarantined": quarantined,
                "filtered": filtered,
                **extra,
            }
        )
        self._flush()

    def record_stage_end(self, stage: str, **extra: Any) -> None:
        self._data["stages"].setdefault(stage, {})
        self._data["stages"][stage]["completed_at"] = datetime.now(tz=timezone.utc).isoformat()
        self._data["stages"][stage].update(extra)
        self._flush()

    def add_cost(self, cost_usd: float, usage: dict[str, int]) -> None:
        """Accumulate token usage and cost per chunk (ST-10)."""
        self._data["cost_usd"] = round(self._data["cost_usd"] + cost_usd, 6)
        for k in ("prompt_tokens", "completion_tokens", "cached_tokens"):
            self._data["token_usage"][k] = self._data["token_usage"].get(k, 0) + usage.get(k, 0)
        self._flush()

    def set_flag(self, key: str, value: Any) -> None:
        """Record an approval flag or acknowledgement (e.g. budget plan approved)."""
        self._data["flags"][key] = value
        self._flush()

    def set_safety_blocks(self, blocks: dict[str, int]) -> None:
        self._data["safety_blocks"] = blocks
        self._flush()

    def complete(self, status: str = "complete") -> None:
        self._data["status"] = status
        self._data["completed_at"] = datetime.now(tz=timezone.utc).isoformat()
        self._flush()

    def _flush(self) -> None:
        """Atomic write: temp file → rename. Safe on kill. (EC-X-05)"""
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(self._path)
