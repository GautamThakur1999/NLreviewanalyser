"""
T-P1-07 - Parquet writer + partitioning.

Writes Verbatim objects to Parquet using an explicit Arrow schema.
Partitioned by source/brand only (shallow hierarchy, EC-X-03).
Uses temp-file-then-rename for atomic writes (EC-X-05/08).

Guards: EC-X-03, EC-X-05, EC-X-08, EC-ST-02, EC-ST-05
"""

import logging
import os
from pathlib import Path
from typing import Sequence

import pyarrow as pa
import pyarrow.parquet as pq

from engine.store.verbatim import Verbatim

logger = logging.getLogger(__name__)

# Define the explicit Arrow schema to prevent drift (EC-ST-02)
VERBATIM_SCHEMA = pa.schema([
    ("verbatim_id", pa.string()),
    ("source", pa.string()),
    ("source_id", pa.string()),
    ("brand", pa.string()),
    ("run_id", pa.string()),
    ("raw_payload_ref", pa.string()),
    ("collected_at", pa.timestamp('ms', tz='UTC')),
    
    ("text_raw", pa.string()),
    ("text_clean", pa.string()),
    ("content_hash", pa.string()),
    ("simhash", pa.uint64()),
    
    ("rating", pa.int32()),
    ("rating_scale", pa.int32()),
    ("lang", pa.string()),
    ("lang_confidence", pa.float64()),
    ("is_romanised", pa.bool_()),
    ("review_date", pa.timestamp('ms', tz='UTC')),
    ("helpful_votes", pa.int32()),
    ("duplicate_count", pa.int32()),
    
    ("thread_id", pa.string()),
    ("parent_id", pa.string()),
    ("depth", pa.int32()),
    
    ("author_hash", pa.string()),
    
    ("thumbs_up", pa.int32()),
    ("quarantine_reason", pa.string()),
])


def write_verbatims_to_parquet(
    verbatims: Sequence[Verbatim],
    data_dir: Path,
    run_id: str
) -> Path:
    """
    Write a batch of verbatims to Parquet.
    Partitioned explicitly as: data/parquet/source={s}/brand={b}/{run_id}.parquet
    """
    if not verbatims:
        raise ValueError("Cannot write empty list of verbatims")
        
    # All verbatims in a batch must share source and brand to go into one partition file
    source = verbatims[0].source
    brand = verbatims[0].brand
    
    for v in verbatims:
        if v.source != source or v.brand != brand:
            raise ValueError("All verbatims in a batch must share source and brand for partitioning")

    # EC-X-03: shallow partitions
    part_dir = data_dir / "parquet" / f"source={source}" / f"brand={brand}"
    part_dir.mkdir(parents=True, exist_ok=True)
    
    final_path = part_dir / f"{run_id}.parquet"
    tmp_path = final_path.with_suffix(".tmp")
    
    # Extract columns
    data = {
        "verbatim_id": [v.verbatim_id for v in verbatims],
        "source": [v.source for v in verbatims],
        "source_id": [v.source_id for v in verbatims],
        "brand": [v.brand for v in verbatims],
        "run_id": [v.run_id for v in verbatims],
        "raw_payload_ref": [v.raw_payload_ref for v in verbatims],
        "collected_at": [v.collected_at for v in verbatims],
        
        "text_raw": [v.text_raw for v in verbatims],
        "text_clean": [v.text_clean for v in verbatims],
        "content_hash": [v.content_hash for v in verbatims],
        "simhash": [v.simhash for v in verbatims],
        
        "rating": [v.rating for v in verbatims],
        "rating_scale": [v.rating_scale for v in verbatims],
        "lang": [v.lang for v in verbatims],
        "lang_confidence": [v.lang_confidence for v in verbatims],
        "is_romanised": [v.is_romanised for v in verbatims],
        "review_date": [v.review_date for v in verbatims],
        "helpful_votes": [v.helpful_votes for v in verbatims],
        "duplicate_count": [v.duplicate_count for v in verbatims],
        
        "thread_id": [v.thread_id for v in verbatims],
        "parent_id": [v.parent_id for v in verbatims],
        "depth": [v.depth for v in verbatims],
        
        "author_hash": [v.author_hash for v in verbatims],
        "thumbs_up": [v.thumbs_up for v in verbatims],
        "quarantine_reason": [v.quarantine_reason for v in verbatims],
    }
    
    table = pa.Table.from_pydict(data, schema=VERBATIM_SCHEMA)
    
    # EC-X-05/08: Atomic write via tmp file
    pq.write_table(table, tmp_path)
    os.replace(tmp_path, final_path)
    
    logger.info(f"Wrote {len(verbatims)} verbatims to {final_path}")
    return final_path
