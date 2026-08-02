"""
T-P2-09 - Deduplication (exact + near).

Rules:
- Scoped within (source, brand).
- If text is SHORT (< floor tokens): collapse only if EXACT match AND identical author_hash.
- If text is LONG (>= floor tokens): collapse if EXACT match OR NEAR match (Hamming <= 3).
- When collapsing, keep the oldest representative and sum duplicate_count.
- Log every collapse with rationale.

Guards: EC-D-01, EC-D-02, EC-D-03, EC-D-04, EC-D-05, EC-C-21, EC-C-28
"""
import logging
from typing import Sequence
from collections import defaultdict

from engine.store.verbatim import Verbatim
from engine.normalise.text import hamming_distance

logger = logging.getLogger(__name__)

NEAR_DEDUP_TOKEN_FLOOR = 8

def deduplicate(verbatims: Sequence[Verbatim]) -> list[Verbatim]:
    """
    Deduplicate a batch of verbatims.
    IMPORTANT: This assumes all verbatims in the batch share the same (source, brand).
    """
    if not verbatims:
        return []

    source = verbatims[0].source
    brand = verbatims[0].brand
    for v in verbatims:
        if v.source != source or v.brand != brand:
            raise ValueError("deduplicate() must be scoped within a single (source, brand)")

    # Sort chronologically so we keep the oldest verbatim as representative
    sorted_verbatims = sorted(verbatims, key=lambda x: x.collected_at)
    
    kept: list[Verbatim] = []
    
    for v in sorted_verbatims:
        is_duplicate = False
        token_count = len(v.text_clean.split())
        kept_idx = -1
        
        for i, k in enumerate(kept):
            # Check exact match
            if v.content_hash == k.content_hash:
                if token_count < NEAR_DEDUP_TOKEN_FLOOR:
                    # Short exact match: only collapse if author is identical
                    if v.author_hash == k.author_hash and v.author_hash is not None:
                        is_duplicate = True
                        kept_idx = i
                        rationale = f"Short exact match, identical author ({v.author_hash})"
                        break
                else:
                    # Long exact match: always collapse
                    is_duplicate = True
                    kept_idx = i
                    rationale = "Long exact match"
                    break
            
            # Check near match (only for long text)
            if token_count >= NEAR_DEDUP_TOKEN_FLOOR:
                if hamming_distance(v.simhash, k.simhash) <= 3:
                    is_duplicate = True
                    kept_idx = i
                    rationale = f"Near match (Hamming <= 3), long text"
                    break

        if is_duplicate:
            logger.info("Collapsed %s into %s: %s", v.verbatim_id, k.verbatim_id, rationale)
            kept[kept_idx] = k.model_copy(update={"duplicate_count": k.duplicate_count + max(1, v.duplicate_count)})
        else:
            kept.append(v)
            
    return kept
