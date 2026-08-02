"""
T-P2-13 - Quarantine store + reconciliation invariant.

Applies cleaning steps to a batch of verbatims:
1. PII stripping (modifies text_raw and text_clean)
2. Spam filtering (flags for quarantine)
3. Empty/URL-only filtering (flags for quarantine)
4. Language identification
5. Deduplication
6. Burst detection

Asserts reconciliation invariant: collected = stored + quarantined + filtered (dedup collapses count towards filtered or just tracked).
Actually, the deduplication collapse reduces the output list size, but we track duplicate_count.
collected = stored + quarantined + (collapsed_count)
"""

import logging
from pathlib import Path
from typing import Sequence

from engine.store.verbatim import Verbatim
from engine.clean.pii import redact_pii
from engine.clean.spam import check_spam
from engine.clean.lang import annotate_language
from engine.clean.dedup import deduplicate
from engine.clean.burst import detect_bursts

logger = logging.getLogger(__name__)

def apply_cleaning_chain(
    verbatims: list[Verbatim], 
    data_dir: Path
) -> tuple[list[Verbatim], list[Verbatim], int]:
    """
    Apply all Chunk 2 cleaning steps.
    Returns (clean_verbatims, quarantined_verbatims, collapsed_count).
    """
    if not verbatims:
        return [], [], 0

    collected_count = len(verbatims)
    
    clean_candidates = []
    quarantined = []
    
    for v in verbatims:
        # 1. PII stripping (before text_raw is frozen)
        # We redact both text_raw and text_clean
        new_text_raw = redact_pii(v.text_raw)
        new_text_clean = redact_pii(v.text_clean)
        
        # Update verbatim (frozen instance, use model_copy)
        v = v.model_copy(update={
            "text_raw": new_text_raw,
            "text_clean": new_text_clean,
            "content_hash": v.content_hash, # content_hash and simhash must be recomputed? Yes!
        })
        
        # We need to recompute hashes after PII stripping because text_clean changed!
        from engine.normalise.text import content_hash, simhash
        v = v.model_copy(update={
            "content_hash": content_hash(new_text_clean),
            "simhash": simhash(new_text_clean),
        })
        
        # 2. Spam filtering
        spam_reason = check_spam(v.text_clean)
        if spam_reason:
            v = v.model_copy(update={"quarantine_reason": spam_reason})
            quarantined.append(v)
            continue
            
        # 3. Empty after clean
        if not v.text_clean.strip():
            v = v.model_copy(update={"quarantine_reason": "empty_after_clean"})
            quarantined.append(v)
            continue
            
        clean_candidates.append(v)
        
    # 4. Language identification
    clean_candidates = annotate_language(clean_candidates)
    
    # 5. Deduplication
    pre_dedup_count = len(clean_candidates)
    clean_candidates = deduplicate(clean_candidates)
    collapsed_count = pre_dedup_count - len(clean_candidates)
    
    # 6. Burst detection
    clean_candidates = detect_bursts(clean_candidates, data_dir)
    
    # Reconciliation assertion (ST-05)
    processed_count = len(clean_candidates) + len(quarantined) + collapsed_count
    
    if collected_count != processed_count:
        logger.error(
            "Reconciliation invariant failed! Collected: %d, Clean: %d, Quarantined: %d, Collapsed: %d",
            collected_count, len(clean_candidates), len(quarantined), collapsed_count
        )
        raise AssertionError("Reconciliation invariant failed: collected != stored + quarantined + collapsed")
        
    return clean_candidates, quarantined, collapsed_count
