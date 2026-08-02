"""
T-P3-03 - Pass A: Open Coding (Inductive)

Draws a stratified sample of RELEVANT verbatims and prompts Gemini Pro to 
extract barriers, drivers, discovery paths, and info needs in free text.
NO candidate list is shown (bottom-up induction).
"""

import json
import logging
import random
from typing import Literal
from pydantic import BaseModel, Field

from engine.llm.gemini_client import GeminiClient
from engine.store.verbatim import Verbatim

logger = logging.getLogger(__name__)

class OpenExtraction(BaseModel):
    verbatim_id: str = Field(..., description="The ID of the verbatim this extraction applies to.")
    barriers: list[str] = Field(default_factory=list, description="Friction points, complaints, or reasons for not using the service.")
    drivers: list[str] = Field(default_factory=list, description="Reasons for using the service, positive experiences, or value drivers.")
    needs: list[str] = Field(default_factory=list, description="Unmet needs or feature requests mentioned.")

class BatchOpenExtraction(BaseModel):
    results: list[OpenExtraction] = Field(..., description="List of extractions matching the input reviews.")

OPEN_CODING_SYSTEM_PROMPT = """You are an expert qualitative researcher doing 'open coding' (grounded theory induction).
You will be given a JSON array of user reviews. For EACH review, extract the key barriers (friction points), drivers (value props), and unmet needs.

CRITICAL INSTRUCTIONS:
- Use FREE TEXT. Do not constrain yourself to any predefined categories.
- Capture the NUANCE of what the user is saying. Use short, descriptive phrases (e.g., "delivery delayed by 30 mins", "produce was rotten", "loved the 10 min speed", "wants better refund process").
- If a category (barrier/driver/need) is not mentioned, leave the list empty.
- OUTPUT FORMAT: You MUST return a JSON object with a single key "results" mapping to a list of your extractions.
- Each extraction object in the list MUST include the "verbatim_id" exactly as provided in the input, along with "barriers", "drivers", and "needs" (not "unmet_needs").
"""

def extract_open_codes_batch(client: GeminiClient, batch: list[Verbatim], model_id: str) -> list[OpenExtraction]:
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
            system=OPEN_CODING_SYSTEM_PROMPT,
            user=user_prompt,
            schema=BatchOpenExtraction,
        )
        return res.parsed.results if res.parsed else []
    except Exception as e:
        logger.error(f"Open Coding LLM error for batch (size {len(batch)}): {e}")
        return []

def extract_open_codes(
    relevant_verbatims: list[Verbatim],
    client: GeminiClient,
    model_id: str,
    sample_size: int = 600
) -> list[tuple[Verbatim, OpenExtraction]]:
    """
    Runs open coding on a stratified sample of relevant verbatims in batches.
    """
    if not relevant_verbatims:
        logger.info("No relevant verbatims to open code.")
        return []
        
    sample = random.sample(relevant_verbatims, min(len(relevant_verbatims), sample_size))
    results = []
    
    batch_size = 5
    for i in range(0, len(sample), batch_size):
        batch = sample[i:i+batch_size]
        extractions = extract_open_codes_batch(client, batch, model_id)
        
        result_map = {e.verbatim_id: e for e in extractions}
        
        for v in batch:
            if v.verbatim_id in result_map:
                results.append((v, result_map[v.verbatim_id]))
                
        logger.info(f"Open coded {min(i+batch_size, len(sample))}/{len(sample)}...")
            
    logger.info(f"Open coding complete for {len(results)} verbatims.")
    return results
