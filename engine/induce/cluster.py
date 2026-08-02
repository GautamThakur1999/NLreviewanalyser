"""
T-P3-04 - Codebook v1 construction

Embeds and clusters the free-text extractions using local sentence-transformers.
Then, simulates "human review" using Gemini to generate the final codebook 
(`v1.yaml`) mapped to the 7 fixed barrier_types.
"""

import os
import yaml
import logging
from pathlib import Path
from pydantic import BaseModel, Field
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer

from engine.llm.gemini_client import GeminiClient
from engine.llm.prompts import build_prompt
from engine.induce.extract import OpenExtraction
from engine.store.verbatim import Verbatim

logger = logging.getLogger(__name__)

# The 7 fixed barrier types from the spec
BARRIER_TYPES = [
    "trust_and_safety",
    "pricing_and_fees",
    "product_availability",
    "quality_and_freshness",
    "delivery_and_logistics",
    "app_ux_and_support",
    "not_a_barrier"
]

class CodeDefinition(BaseModel):
    name: str = Field(..., description="Short, descriptive snake_case name for the code.")
    barrier_type: str = Field(..., description="One of the 7 fixed barrier types.")
    definition: str = Field(..., description="Clear, exhaustive definition of what this code covers.")
    inclusion_rule: str = Field(..., description="When to apply this code.")
    exclusion_rule: str = Field(..., description="When NOT to apply this code.")
    exemplars: list[str] = Field(..., description="3 examples of user quotes fitting this code.")

class CodebookV1(BaseModel):
    version: str = "v1"
    codes: list[CodeDefinition] = Field(..., description="List of all induced codes.")

CODEBOOK_PROMPT = f"""You are the lead qualitative researcher. I have clustered hundreds of free-text barriers/drivers extracted from user reviews.
Review these clusters and synthesize them into a formal Codebook (v1). Output your response in valid JSON.

CRITICAL CONSTRAINTS:
Every code MUST map to exactly one of these 7 fixed barrier types:
{BARRIER_TYPES}

For each code, provide a snake_case name, the matching barrier_type, a clear definition, inclusion/exclusion rules, and 3 realistic exemplar quotes.
Create a comprehensive but distinct set of codes based ONLY on these clusters. Do not invent codes that aren't represented in the data.

OUTPUT FORMAT:
Your JSON must strictly match the following schema exactly.
You MUST return an object with a single key "codes" which is a list of objects.
Each object MUST have the following EXACT keys:
- "name"
- "barrier_type" 
- "definition"
- "inclusion_rule" (DO NOT use inclusion_exclusion)
- "exclusion_rule"
- "exemplars" (DO NOT use exemplar_quotes)
"""

def cluster_and_induce_codebook(
    extractions: list[tuple[Verbatim, OpenExtraction]],
    client: GeminiClient,
    model_id: str,
    output_dir: Path
) -> Path:
    """
    1. Flattens all extracted phrases.
    2. Embeds with sentence-transformers.
    3. Clusters with AgglomerativeClustering.
    4. Passes clusters to Gemini to induce v1.yaml.
    """
    if not extractions:
        raise ValueError("No extractions provided for clustering.")
        
    # Flatten all text
    phrases = []
    for _, ext in extractions:
        phrases.extend(ext.barriers)
        phrases.extend(ext.drivers)
        phrases.extend(ext.needs)
        
    # Deduplicate loosely and filter empty
    phrases = list(set([p.strip() for p in phrases if len(p.strip()) > 3]))
    logger.info(f"Clustering {len(phrases)} unique extracted phrases...")
    
    if len(phrases) < 5:
        logger.warning("Too few phrases to cluster effectively.")
        clusters_text = "\\n".join(phrases)
    else:
        # Use TF-IDF instead of sentence-transformers to avoid PyTorch DLL issues on Windows
        vectorizer = TfidfVectorizer(stop_words='english')
        embeddings = vectorizer.fit_transform(phrases).toarray()
        
        # Use Agglomerative clustering to find semantic groups
        clusterer = AgglomerativeClustering(n_clusters=None, distance_threshold=1.2, metric='euclidean', linkage='ward')
        labels = clusterer.fit_predict(embeddings)
        
        # Group phrases by label
        clusters = {}
        for phrase, label in zip(phrases, labels):
            clusters.setdefault(label, []).append(phrase)
            
        logger.info(f"Formed {len(clusters)} clusters.")
        
        # Format clusters for the prompt
        cluster_blocks = []
        for label, items in clusters.items():
            cluster_blocks.append(f"Cluster {label}:\n- " + "\n- ".join(items[:10])) # Max 10 per cluster for context limit
        clusters_text = "\n\n".join(cluster_blocks)

    # 5. Gemini "Human Review" Proxy
    logger.info("Simulating human review to build v1.yaml...")
    # Wrap in our standard format manually since it's not a single Verbatim
    res = client.complete_structured(
        system=CODEBOOK_PROMPT,
        user=f"<CLUSTERS>\n{clusters_text}\n</CLUSTERS>",
        schema=CodebookV1,
    )
    
    codebook = res.parsed
    if not codebook:
        raise RuntimeError("Failed to induce codebook from Gemini.")
        
    # 6. Save to YAML
    out_file = output_dir / "v1.yaml"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(codebook.model_dump(), f, sort_keys=False, allow_unicode=True)
        
    logger.info(f"Codebook v1 saved to {out_file}")
    return out_file
