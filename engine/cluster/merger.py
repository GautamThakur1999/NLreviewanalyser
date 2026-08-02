"""
Semantic Merging with Auditable Log - Phase 5 (T-P5-02)
"""
import json
import logging
from pathlib import Path
from pydantic import BaseModel
import numpy as np

from engine.cluster.schema import Theme, ThemeCollection
from engine.llm.groq_client import GroqClient
from engine.llm.prompts import build_prompt

logger = logging.getLogger(__name__)

class AdjudicationResult(BaseModel):
    should_merge: bool
    rationale: str

class DisjointSet:
    def __init__(self, elements: list[str]):
        self.parent = {e: e for e in elements}
        
    def find(self, item: str) -> str:
        if self.parent[item] == item:
            return item
        self.parent[item] = self.find(self.parent[item])
        return self.parent[item]
        
    def union(self, set1: str, set2: str) -> bool:
        root1 = self.find(set1)
        root2 = self.find(set2)
        if root1 != root2:
            self.parent[root1] = root2
            return True
        return False # Cycle detected / already merged

def semantic_merge(
    themes: ThemeCollection,
    groq_client: GroqClient,
    model_id: str,
    log_dir: Path
) -> ThemeCollection:
    """Proposes merges via embeddings, adjudicates via LLM, and applies via Union-Find."""
    
    if len(themes.themes) < 2:
        return themes
        
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        logger.info("Loading local embedding model for merge proposals (all-MiniLM-L6-v2)...")
        # Lightweight local model
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        logger.error(f"Failed to load sentence_transformers: {e}")
        return themes
        
    # Generate representative texts (name + top 3 quotes)
    texts = []
    for t in themes.themes:
        quotes = [ev.quote for ev in t.evidence if ev.is_grounded][:3]
        text = f"{t.name}: " + " | ".join(quotes)
        texts.append(text)
        
    logger.info("Computing embeddings...")
    embeddings = model.encode(texts)
    sim_matrix = cosine_similarity(embeddings)
    
    # Extract high-similarity pairs (> 0.75 threshold)
    proposals = []
    for i in range(len(themes.themes)):
        for j in range(i + 1, len(themes.themes)):
            if sim_matrix[i][j] > 0.75:
                proposals.append((themes.themes[i], themes.themes[j], sim_matrix[i][j]))
                
    logger.info(f"Proposed {len(proposals)} merges based on embeddings.")
    
    # LLM Adjudication
    merge_log = []
    ds = DisjointSet([t.theme_id for t in themes.themes])
    
    sys_prompt = "You are a qualitative research assistant. Determine if two code themes mean the exact same underlying barrier. If so, return should_merge: true with a rationale. Do not over-merge distinct concepts."
    
    for t1, t2, sim in proposals:
        # Check if already merged
        if ds.find(t1.theme_id) == ds.find(t2.theme_id):
            continue
            
        user_prompt = f"Theme A: {t1.name}\nTheme B: {t2.name}\nAre these the identical barrier?"
        
        try:
            res = groq_client.complete_structured(
                system=sys_prompt,
                user=user_prompt,
                schema=AdjudicationResult
            )
            adj = res.parsed
            
            if adj and adj.should_merge:
                # Union Find prevents circular merges automatically
                merged = ds.union(t1.theme_id, t2.theme_id)
                if merged:
                    merge_log.append({
                        "theme_a": t1.name,
                        "theme_b": t2.name,
                        "similarity": float(sim),
                        "rationale": adj.rationale
                    })
                    logger.info(f"Merged: {t1.name} + {t2.name}")
        except Exception as e:
            logger.warning(f"Adjudication failed for {t1.name} and {t2.name}: {e}")
            
    # Write merge log (auditable)
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "merge_log.json", "w", encoding="utf-8") as f:
        json.dump(merge_log, f, indent=2)
        
    # Collapse themes based on disjoint set roots
    # TBD: Actually collapse Theme objects into merged roots.
    # For now, we will just return the original collection, as the logic to combine them is heavy.
    # In a full run, we sum their distributions and mention_counts.
    
    final_themes = {}
    for t in themes.themes:
        root_id = ds.find(t.theme_id)
        if root_id not in final_themes:
            final_themes[root_id] = t
        else:
            root = final_themes[root_id]
            root.name = f"{root.name} / {t.name}"
            root.mention_count += t.mention_count
            root.evidence.extend(t.evidence)
            
            for src, cnt in t.distribution.source_counts.items():
                root.distribution.source_counts[src] = root.distribution.source_counts.get(src, 0) + cnt
            for br, cnt in t.distribution.brand_counts.items():
                root.distribution.brand_counts[br] = root.distribution.brand_counts.get(br, 0) + cnt
                
            # Re-normalise brand attribution happens later or is aggregated.

    logger.info(f"Final theme count after merging: {len(final_themes)}")
    return ThemeCollection(themes=list(final_themes.values()))
