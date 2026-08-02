"""
Theme Aggregation - Phase 5
"""
import logging
from pathlib import Path
from engine.label.schema import Label
from engine.cluster.schema import Theme, ThemeEvidence, ThemeDistribution, ThemeCollection
from engine.induce.runner import load_clean_verbatims

logger = logging.getLogger(__name__)

def aggregate_themes(labels: list[Label], verbatims_dir: Path) -> ThemeCollection:
    """
    Groups atomic labels into Themes, computing first_seen and distributions.
    Brand normalisation (T-P5-03) is applied to prevent volume skew.
    """
    logger.info("Loading verbatims to map metadata...")
    verbatims = load_clean_verbatims(verbatims_dir, "")
    v_map = {v.verbatim_id: v for v in verbatims}
    
    # We sort all labels by the verbatim's timestamp to calculate `first_seen_at_doc_n` deterministically.
    # We assign doc_n as the chronological rank of the review.
    # If review_date is missing, we use a fallback of 0.
    labels_with_meta = []
    total_brand_volume = {}
    for lbl in labels:
        v = v_map.get(lbl.verbatim_id)
        if v:
            # T-P5-03: Track total corpus volume per brand (among the sampled labels)
            total_brand_volume[v.brand] = total_brand_volume.get(v.brand, 0) + 1
            ts = v.review_date.timestamp() if v.review_date else 0
            labels_with_meta.append((ts, lbl, v))
            
    labels_with_meta.sort(key=lambda x: x[0])
    
    # Group by code_name
    theme_map: dict[str, Theme] = {}
    
    for doc_n, (_, lbl, v) in enumerate(labels_with_meta):
        for assigned in lbl.assigned_codes:
            code = assigned.code_name
            if code not in theme_map:
                theme_map[code] = Theme(
                    theme_id=code,
                    name=code,
                    barrier_type=assigned.barrier_type,
                    first_seen_at_doc_n=doc_n
                )
            
            theme = theme_map[code]
            theme.mention_count += 1
            
            # Update distributions
            theme.distribution.source_counts[v.source] = theme.distribution.source_counts.get(v.source, 0) + 1
            theme.distribution.brand_counts[v.brand] = theme.distribution.brand_counts.get(v.brand, 0) + 1
            
            # Add evidence
            for span in assigned.evidence:
                theme.evidence.append(
                    ThemeEvidence(
                        verbatim_id=v.verbatim_id,
                        quote=span.quote,
                        start=span.start,
                        end=span.end,
                        is_grounded=span.is_grounded
                    )
                )

    # T-P5-03: Brand Volume Normalisation
    # If a theme has 10 mentions for Blinkit and 5 for Zepto, but Blinkit has 1000 reviews and Zepto has 100,
    # then the normalized attribution is Blinkit: (10/1000)=0.01 vs Zepto: (5/100)=0.05
    for theme in theme_map.values():
        norm_totals = {}
        for brand, count in theme.distribution.brand_counts.items():
            corpus_vol = total_brand_volume.get(brand, 1)
            norm_totals[brand] = count / corpus_vol
            
        sum_norm = sum(norm_totals.values())
        if sum_norm > 0:
            for brand, norm_val in norm_totals.items():
                theme.distribution.brand_attribution[brand] = round((norm_val / sum_norm) * 100, 2)
                
    logger.info(f"Aggregated {len(theme_map)} unique themes from {len(labels)} documents.")
    return ThemeCollection(themes=list(theme_map.values()))
