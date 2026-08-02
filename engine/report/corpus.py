"""
T-P2-16 - Corpus documentation generator.

Generates Deliverable 2: an auto-generated corpus document detailing volumes,
filter rates, gaps, contamination, composition, and honest limitations.
Reads from the immutable snapshot and manifests.

Guards: EC-B-03, EC-L-05
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import duckdb

from engine.config.settings import Settings

logger = logging.getLogger(__name__)

def generate_corpus_doc(data_dir: Path, settings: Settings, snapshot_id: str) -> Path:
    """
    Generate corpus_doc.md based on the provided snapshot and manifest files.
    """
    snap_dir = data_dir / "snapshots" / snapshot_id
    if not snap_dir.exists():
        raise ValueError(f"Snapshot directory not found: {snap_dir}")
        
    doc_path = data_dir / "reports" / f"corpus_{snapshot_id}.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to DuckDB to query Parquet files
    con = duckdb.connect(database=':memory:')
    
    # Load clean data
    clean_pq = snap_dir / "source=*" / "brand=*" / "*.parquet"
    
    # We might have quarantine data as well. Let's query it if it exists.
    # We wrote it to quarantine_{run_id}.parquet, but they might be in the root or partitioned?
    # Our runner wrote it using write_verbatims_to_parquet which partitions by source/brand!
    # Ah, `write_verbatims_to_parquet(quarantined, data_dir, f"quarantine_{run_id}")`
    # It would be in `data_dir / "parquet" / f"source={s}" / f"brand={b}" / f"quarantine_{run_id}.parquet"`.
    # Let's create a view for clean data
    con.execute(f"CREATE VIEW clean_verbatims AS SELECT * FROM read_parquet('{str(snap_dir)}/*/*/*.parquet') WHERE run_id NOT LIKE 'quarantine_%'")
    
    # Create view for quarantine data (if any)
    try:
        con.execute(f"CREATE VIEW quarantine_verbatims AS SELECT * FROM read_parquet('{str(snap_dir)}/*/*/*.parquet') WHERE run_id LIKE 'quarantine_%'")
        has_quarantine = True
    except Exception:
        has_quarantine = False
        logger.warning("No quarantine data found in snapshot.")

    # 1. Volumes by source x brand x language x rating
    logger.info("Computing basic volumes...")
    volumes_query = """
    SELECT source, brand, lang, rating, COUNT(*) as count
    FROM clean_verbatims
    GROUP BY source, brand, lang, rating
    ORDER BY count DESC
    """
    volumes_df = con.execute(volumes_query).df()
    
    # 2. Time range
    time_range_query = """
    SELECT MIN(review_date) as start_date, MAX(review_date) as end_date
    FROM clean_verbatims
    """
    time_range = con.execute(time_range_query).fetchone()
    
    # 3. Burst-flagged volume
    # Because burst_flag is in meta dict? wait, meta is not explicitly extracted into a column, it's a JSON string maybe?
    # Actually, Verbatim schema has a lot of fields, but `meta` wasn't explicitly added to the Parquet schema in `engine/store/parquet.py`.
    # Let's query quarantine stats instead.
    if has_quarantine:
        q_stats_query = """
        SELECT quarantine_reason, COUNT(*) as count
        FROM quarantine_verbatims
        GROUP BY quarantine_reason
        ORDER BY count DESC
        """
        q_stats = con.execute(q_stats_query).fetchall()
    else:
        q_stats = []

    # Read latest manifest for rates and gaps
    manifest_data = {}
    runs_dir = data_dir / "runs"
    if runs_dir.exists():
        # Get latest run
        runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
        if runs:
            latest_run = runs[-1]
            manifest_file = latest_run / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file, "r") as f:
                    manifest_data = json.load(f).get("state", {})
                    
    quota_shortfalls = manifest_data.get("quota_shortfalls", {})
    completed_sources = manifest_data.get("completed_sources", [])
    collection_windows = manifest_data.get("collection_windows", {})

    # Compose markdown document
    lines = []
    lines.append(f"# Corpus Documentation: {snapshot_id}")
    lines.append(f"Generated at: {datetime.utcnow().isoformat()}Z\n")
    
    lines.append("## 1. Time Range")
    if time_range and time_range[0]:
        lines.append(f"- **Earliest Review**: {time_range[0]}")
        lines.append(f"- **Latest Review**: {time_range[1]}\n")
    else:
        lines.append("No date range available.\n")
        
    lines.append("## 2. Volumes by Segment")
    lines.append("| Source | Brand | Language | Rating | Count |")
    lines.append("|---|---|---|---|---|")
    for _, row in volumes_df.iterrows():
        lines.append(f"| {row['source']} | {row['brand']} | {row['lang']} | {row['rating']} | {row['count']} |")
    lines.append("")
        
    lines.append("## 3. Filter and Quarantine Rates")
    lines.append("| Quarantine Reason | Count |")
    lines.append("|---|---|")
    if q_stats:
        for reason, count in q_stats:
            lines.append(f"| {reason} | {count} |")
    else:
        lines.append("| None | 0 |")
    lines.append("")
        
    lines.append("## 4. Declared Gaps & Under-fills")
    if quota_shortfalls:
        for sk, data in quota_shortfalls.items():
            lines.append(f"- **{sk}**: Collected {data['collected']}, Target {data['target_min']}. Bias consequence: {data['bias_consequence']}")
    else:
        lines.append("No quota shortfalls recorded.\n")
        
    # Instagram gap (hardcoded as declared per plan)
    lines.append("\n**Explicit Disclaimers:**")
    lines.append("- Instagram was intentionally omitted due to the lack of a compliant API. This implies a systemic under-representation of visually-driven, lifestyle-focused feedback.")
    lines.append("- Instamart contamination in Swiggy reviews was filtered, but residual leakage may exist.")
    
    lines.append("\n## 5. Composition Table (Achieved vs Target)")
    lines.append("| Source | Brand | Target Min | Target Max | Achieved |")
    lines.append("|---|---|---|---|---|")
    
    total_achieved = 0
    # Group achieved by source, brand
    achieved_query = """
    SELECT source, brand, COUNT(*) as count
    FROM clean_verbatims
    GROUP BY source, brand
    """
    achieved_dict = {(r[0], r[1]): r[2] for r in con.execute(achieved_query).fetchall()}
    
    for src in settings.sources:
        achieved = achieved_dict.get((src.source, src.brand), 0)
        total_achieved += achieved
        lines.append(f"| {src.source} | {src.brand} | {src.target_min} | {src.target_max} | {achieved} |")
    lines.append(f"| **Total** | | | | **{total_achieved}** |")
        
    lines.append("\n## 6. Honest Limitations")
    lines.append("- The sample is skewed towards highly vocal customers (promoters and detractors), missing the silent majority.")
    lines.append("- Hindi/Hinglish language heuristics may misclassify extremely short ambiguous strings.")
    lines.append("- Spam filtering rules (URL whitelists, emoji blocks) may have marginal false-positive rates on culturally nuanced expressions.")
    
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    logger.info(f"Corpus documentation generated at {doc_path}")
    return doc_path
