"""
T-P3-05 - Residue check (The falsification test)

Runs a pilot labelling pass (Pass B) on a sample of relevant verbatims using 
the newly generated codebook v1. Measures the "residue rate" - the share of 
relevant verbatims that were assigned NO codes (excluding `not_a_barrier`).
If residue is high (>15%), it suggests the codebook missed something real.
"""

import json
import logging
import random
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

from engine.llm.gemini_client import GeminiClient
from engine.store.verbatim import Verbatim
from engine.store.manifest import Manifest

logger = logging.getLogger(__name__)

class PilotLabel(BaseModel):
    verbatim_id: str = Field(..., description="The ID of the verbatim this label applies to.")
    assigned_codes: list[str] = Field(..., description="List of snake_case code names assigned to this verbatim based on the codebook.")
    reasoning: str = Field(..., description="Brief reasoning for why these codes were assigned.")

class BatchPilotLabel(BaseModel):
    results: list[PilotLabel] = Field(..., description="List of labels matching the input reviews.")

def run_residue_check_batch(
    client: GeminiClient, 
    batch: list[Verbatim], 
    system_prompt: str, 
    model_id: str
) -> list[PilotLabel]:
    inputs = []
    for v in batch:
        inputs.append({
            "verbatim_id": v.verbatim_id,
            "text": v.text_clean or v.text_raw,
            "rating": v.rating,
            "source": v.source
        })
    user_prompt = json.dumps(inputs, ensure_ascii=False)
    
    try:
        res = client.complete_structured(
            system=system_prompt,
            user=user_prompt,
            schema=BatchPilotLabel,
        )
        return res.parsed.results if res.parsed else []
    except Exception as e:
        logger.error(f"Residue Check LLM error for batch (size {len(batch)}): {e}")
        return []

def run_residue_check(
    relevant_verbatims: list[Verbatim],
    client: GeminiClient,
    model_id: str,
    codebook_path: Path,
    manifest: Manifest,
    sample_size: int = 50
) -> dict:
    """
    Runs a pilot labelling pass to measure codebook residue in batches.
    """
    if not codebook_path.exists():
        raise FileNotFoundError(f"Codebook not found at {codebook_path}")
        
    with open(codebook_path, "r", encoding="utf-8") as f:
        codebook_yaml = f.read()
        
    if not relevant_verbatims:
        logger.info("No relevant verbatims to check.")
        return {}
        
    sample = random.sample(relevant_verbatims, min(len(relevant_verbatims), sample_size))
    
    SYSTEM_PROMPT = f"""You are an expert qualitative coder.
Apply the following codebook to the user reviews provided as a JSON array. 

<CODEBOOK>
{codebook_yaml}
</CODEBOOK>

For EACH review, assign any codes that apply. If the review is relevant but fits NONE of the codes, return an empty list for assigned_codes. 
Do NOT invent new codes. Only use the names defined in the codebook.
"""

    total_residue = 0
    results = []
    
    batch_size = 25
    for i in range(0, len(sample), batch_size):
        batch = sample[i:i+batch_size]
        labels = run_residue_check_batch(client, batch, SYSTEM_PROMPT, model_id)
        
        result_map = {l.verbatim_id: l for l in labels}
        
        for v in batch:
            if v.verbatim_id in result_map:
                res = result_map[v.verbatim_id]
                codes = res.assigned_codes
                if len(codes) == 0:
                    total_residue += 1
                    logger.warning(f"Residue (No codes fit): {v.text_clean}")
                results.append((v, res))
                
    if len(sample) == 0:
        return {}
        
    residue_rate = (total_residue / len(sample)) * 100
    logger.info(f"Residue Rate: {residue_rate:.1f}% ({total_residue}/{len(sample)})")
    
    stats = {
        "residue_rate_pct": residue_rate,
        "sample_size": len(sample),
        "residue_count": total_residue,
        "codebook_version": "v1"
    }
    
    manifest._data["residue_stats"] = stats
    manifest._flush()
    
    return stats
