"""
T-P2-11 - Incentivised-campaign / burst detection.

Reads cross-run historical partition metadata to detect sudden spikes in 5-star ratings
(>= 3x the trailing 7-day average volume in a 24-hour window).
Tags all reviews in that window with burst_flag=True.

Guards: EC-D-15
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Sequence

import pyarrow.parquet as pq

from engine.store.verbatim import Verbatim

logger = logging.getLogger(__name__)

def _is_5_star(rating: int | None, scale: int) -> bool:
    if rating is None or scale <= 0:
        return False
    # If 5-star scale, rating=5 is 5-star. 
    # If 10-star scale, rating=10 is max. 
    # The requirement is specifically "5-star ratings", but let's assume max rating.
    return rating == scale

def detect_bursts(verbatims: Sequence[Verbatim], data_dir: Path) -> list[Verbatim]:
    """
    Detect bursts and annotate verbatims inplace. Returns the annotated list.
    """
    if not verbatims:
        return list(verbatims)
        
    source = verbatims[0].source
    brand = verbatims[0].brand
    
    # Histogram of max-rating reviews by day
    # day -> count
    history_counts: dict[date, int] = defaultdict(int)
    
    # 1. Load historical counts from Parquet
    part_dir = data_dir / "parquet" / f"source={source}" / f"brand={brand}"
    if part_dir.exists():
        for pq_file in part_dir.glob("*.parquet"):
            try:
                # We only need review_date, collected_at, rating, rating_scale
                table = pq.read_table(
                    pq_file, 
                    columns=["review_date", "collected_at", "rating", "rating_scale"]
                )
                
                # Convert to Python lists
                dates_col = table["review_date"].to_pylist()
                col_dates_col = table["collected_at"].to_pylist()
                ratings_col = table["rating"].to_pylist()
                scales_col = table["rating_scale"].to_pylist()
                
                for r_date, c_date, rating, scale in zip(dates_col, col_dates_col, ratings_col, scales_col):
                    if _is_5_star(rating, scale):
                        dt = r_date if r_date else c_date
                        if dt:
                            history_counts[dt.date()] += 1
            except Exception as e:
                logger.warning("Failed to read parquet file %s for burst detection: %s", pq_file, e)

    # 2. Add current run's verbatims to the histogram
    # But wait, to be accurate, we only add them if they aren't already in the parquet files.
    # Since we are processing them BEFORE writing to parquet, they are definitely not in parquet yet.
    current_run_counts: dict[date, int] = defaultdict(int)
    for v in verbatims:
        dt = v.review_date if v.review_date else v.collected_at
        if dt and _is_5_star(v.rating, v.rating_scale):
            current_run_counts[dt.date()] += 1
            
    # Merge current run into history (so the spike calculation sees the new total for today)
    for d, count in current_run_counts.items():
        history_counts[d] += count

    # 3. Detect bursts and tag
    annotated = []
    
    # Cache if a date is a burst
    burst_days: dict[date, bool] = {}
    
    for v in verbatims:
        dt = v.review_date if v.review_date else v.collected_at
        if not dt:
            annotated.append(v)
            continue
            
        d = dt.date()
        
        if d not in burst_days:
            # Calculate trailing 7 days average (D-7 to D-1)
            trailing_sum = 0
            for i in range(1, 8):
                prev_d = d - timedelta(days=i)
                trailing_sum += history_counts[prev_d]
                
            avg_trailing = trailing_sum / 7.0
            today_count = history_counts[d]
            
            # Spike condition: >= 3x trailing average AND a minimum absolute volume (e.g., to avoid 1 -> 3 spikes)
            # We assume a minimum trailing average of 1 so 3x means at least 3 reviews.
            # But let's set a floor: if average is 0, we require at least 5 reviews to call it a burst.
            if avg_trailing < 1.0:
                is_burst = today_count >= 5
            else:
                is_burst = today_count >= (3 * avg_trailing)
                
            burst_days[d] = is_burst
            
        if burst_days[d]:
            # It's a burst! Tag the verbatim.
            # Using dict copy to prevent mutating the original reference if it's frozen, wait, Verbatim is frozen!
            # So we use model_copy
            meta = dict(v.meta or {})
            meta["burst_flag"] = True
            annotated.append(v.model_copy(update={"meta": meta}))
        else:
            annotated.append(v)
            
    return annotated
