"""
T-P1-02 - Raw archive writer (raw-first).

Gzipped JSONL per (run_id, source, brand).
Returns a raw_payload_ref for each written line.

Guards: EC-C-16, EC-C-14
"""

import gzip
import json
from pathlib import Path
from typing import Any

from engine.store.manifest import make_run_id


class RawArchiveWriter:
    """
    Append-only writer for raw JSON payloads.
    Writes to data/raw/{run_id}/{source}_{brand}.jsonl.gz.
    """

    def __init__(self, run_id: str, source: str, brand: str, data_dir: Path):
        self.run_id = run_id
        self.source = source
        self.brand = brand
        
        # Determine paths
        self.run_dir = data_dir / "raw" / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.filename = f"{source}_{brand}.jsonl.gz"
        self.filepath = self.run_dir / self.filename
        
        # Track line number to generate references
        self._line_count = 0

    def write(self, payload: dict[str, Any]) -> str:
        """
        Write the raw payload to the gzipped JSONL file.
        Returns the raw_payload_ref.
        """
        # We append to the gzip file. Opening in 'at' mode is supported.
        # But for performance and safety if the file is kept open, we can just open/close 
        # or keep a handle open. For simplicity and robustness across iterations,
        # we'll open it per batch or keep it open. A context manager is best.
        raise NotImplementedError("Use context manager")
        
    def __enter__(self):
        self._file = gzip.open(self.filepath, "at", encoding="utf-8")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()
        
    def write_payload(self, payload: dict[str, Any]) -> str:
        """
        Write a single payload and return its reference string.
        """
        self._line_count += 1
        line = json.dumps(payload, ensure_ascii=False, default=str)
        self._file.write(line + "\n")
        
        # Ref format: '{run_id}/{source}_{brand}.jsonl.gz#L{n}'
        return f"{self.run_id}/{self.filename}#L{self._line_count}"
