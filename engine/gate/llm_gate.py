"""
T-P3-01 - Tier-1 relevance gate (Groq)

Filters the prefiltered corpus to only verbatims relevant to quick-commerce
category exploration, barriers, drivers, or unmet needs. Excluded verbatims
are retained as `gate_irrelevant`.
"""

import json
import logging
from typing import Literal
from pydantic import BaseModel, Field

from engine.llm.groq_client import GroqClient
from engine.llm.prompts import build_single_prompt
from engine.store.verbatim import Verbatim
from engine.config.settings import Settings

logger = logging.getLogger(__name__)

class GateResult(BaseModel):
    verbatim_id: str = Field(..., description="The ID of the verbatim this result applies to.")
    is_relevant: bool = Field(..., description="True if the review discusses quick-commerce delivery, products, app experience, pricing, or customer service.")
    relevance_reason: str = Field(..., description="Brief reason for relevance or irrelevance (<= 10 words).")
    primary_topic: str = Field(..., description="The main topic (e.g., 'delivery time', 'refund', 'app UI', 'unknown').")

class BatchGateResult(BaseModel):
    results: list[GateResult] = Field(..., description="List of gate results matching the input reviews.")

GATE_SYSTEM_PROMPT = """You are an expert data annotator.
Your job is to gate user reviews for a quick-commerce (10-minute grocery delivery) app.
You will be given a JSON array of reviews. You must evaluate EACH review.

A review is RELEVANT if it mentions:
- Delivery speed, delays, or experience
- Product quality, missing items, or packaging
- Pricing, fees, refunds, or discounts
- App usability, customer support, or driver behaviour
- Comparisons between services (Blinkit, Zepto, Swiggy, etc.)

If the review is about ANY of these topics, mark it RELEVANT.
If it is just "good app", "bad", or completely unrelated to quick-commerce, mark IRRELEVANT.

Output in JSON format matching this EXACT schema:
{
  "results": [
    {
      "verbatim_id": "the_id_from_input",
      "is_relevant": true or false,
      "relevance_reason": "Brief reason for relevance or irrelevance (<= 10 words)",
      "primary_topic": "The main topic (e.g., 'delivery time', 'refund', 'app UI', 'unknown')"
    }
  ]
}
"""

def evaluate_relevance_batch(client: GroqClient, batch: list[Verbatim], model_id: str) -> list[GateResult]:
    """
    Evaluates a batch of verbatims for relevance using Groq semantic batching.
    """
    # Construct JSON array of inputs
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
        result = client.complete_structured(
            system=GATE_SYSTEM_PROMPT,
            user=user_prompt,
            schema=BatchGateResult,
            max_tokens=4096
        )
        return result.parsed.results
    except Exception as e:
        logger.error(f"Gate LLM error for batch (size {len(batch)}): {e}")
        return []

def run_llm_gate(
    verbatims: list[Verbatim], 
    client: GroqClient, 
    model_id: str
) -> tuple[list[Verbatim], list[Verbatim]]:
    """
    Splits verbatims into (relevant, irrelevant) using the LLM gate (in batches of 50).
    """
    relevant = []
    irrelevant = []
    
    batch_size = 20
    for i in range(0, len(verbatims), batch_size):
        batch = verbatims[i:i+batch_size]
        results = evaluate_relevance_batch(client, batch, model_id)
        
        # Match results back to verbatims by ID
        result_map = {r.verbatim_id: r for r in results}
        
        for v in batch:
            res = result_map.get(v.verbatim_id)
            if res is None:
                # If API fails for this item, keep it for recall (fail open)
                relevant.append(v)
            elif res.is_relevant:
                relevant.append(v)
            else:
                irrelevant.append(v)
                
        logger.info(f"Gated {min(i+batch_size, len(verbatims))}/{len(verbatims)}...")
            
    logger.info(f"LLM Gate: {len(relevant)} passed, {len(irrelevant)} excluded")
    return relevant, irrelevant
