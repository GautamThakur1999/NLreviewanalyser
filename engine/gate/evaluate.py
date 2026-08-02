"""
T-P3-02 - Gate false-negative measurement.

Evaluates a sample of gate-rejected verbatims using Gemini (as a proxy for 
human review) to measure the False Negative (FN) rate of the Tier-1 Groq gate.
"""

import json
import logging
import random
from typing import Literal
from pydantic import BaseModel, Field

from engine.llm.gemini_client import GeminiClient
from engine.store.verbatim import Verbatim
from engine.store.manifest import Manifest

logger = logging.getLogger(__name__)

class FNReviewResult(BaseModel):
    verbatim_id: str = Field(..., description="The ID of the verbatim this result applies to.")
    is_actually_relevant: bool = Field(..., description="True if the review is ACTUALLY relevant, meaning the Groq gate made a False Negative error.")
    reason: str = Field(..., description="Why is it relevant or not?")

class BatchFNReviewResult(BaseModel):
    results: list[FNReviewResult] = Field(..., description="List of results matching the input reviews.")

FN_SYSTEM_PROMPT = """You are an expert qualitative researcher acting as the 'Gold Standard' human reviewer.
Your job is to double-check documents that a cheaper AI (Groq) rejected as IRRELEVANT.
You will receive a JSON array of reviews. Evaluate EACH one.

A review is RELEVANT if it mentions:
- Delivery speed, delays, or experience
- Product quality, missing items, or packaging
- Pricing, fees, refunds, or discounts
- App usability, customer support, or driver behaviour
- Comparisons between services (Blinkit, Zepto, Swiggy, etc.)

We want to measure the False Negative rate. If you think a review IS plausibly related to quick-commerce (even tangentially), mark `is_actually_relevant = true` and provide a `reason`.
OUTPUT FORMAT: You MUST return a JSON object with a single key "results" mapping to a list of your evaluations.
"""

def evaluate_gate_fns_batch(client: GeminiClient, batch: list[Verbatim], model_id: str) -> list[FNReviewResult]:
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
            system=FN_SYSTEM_PROMPT,
            user=user_prompt,
            schema=BatchFNReviewResult,
        )
        return res.parsed.results if res.parsed else []
    except Exception as e:
        logger.error(f"FN Eval LLM error for batch (size {len(batch)}): {e}")
        return []

def evaluate_gate_fns(
    irrelevant_verbatims: list[Verbatim],
    client: GeminiClient,
    model_id: str,
    manifest: Manifest,
    sample_size: int = 50
) -> dict:
    """
    Draws a stratified sample of irrelevant verbatims and measures the FN rate in batches.
    """
    if not irrelevant_verbatims:
        logger.info("No irrelevant verbatims to evaluate.")
        return {}
        
    sample = random.sample(irrelevant_verbatims, min(len(irrelevant_verbatims), sample_size))
    
    total_fns = 0
    fns_by_lang = {}
    total_by_lang = {}
    
    batch_size = 25
    for i in range(0, len(sample), batch_size):
        batch = sample[i:i+batch_size]
        
        for v in batch:
            lang = v.lang or "unknown"
            total_by_lang[lang] = total_by_lang.get(lang, 0) + 1
            
        results = evaluate_gate_fns_batch(client, batch, model_id)
        result_map = {r.verbatim_id: r for r in results}
        
        for v in batch:
            if v.verbatim_id in result_map:
                res = result_map[v.verbatim_id]
                if res.is_actually_relevant:
                    total_fns += 1
                    lang = v.lang or "unknown"
                    fns_by_lang[lang] = fns_by_lang.get(lang, 0) + 1
                    logger.warning(f"False Negative found ({lang}): {v.text_clean} -> {res.reason}")
                    
    if len(sample) == 0:
        return {}
        
    fn_rate = (total_fns / len(sample)) * 100
    logger.info(f"Gate FN Rate: {fn_rate:.1f}% ({total_fns}/{len(sample)})")
    
    lang_rates = {}
    for lang, count in total_by_lang.items():
        lang_fns = fns_by_lang.get(lang, 0)
        rate = (lang_fns / count) * 100
        lang_rates[lang] = {"fns": lang_fns, "total": count, "rate_pct": rate}
        logger.info(f"  - {lang} FN Rate: {rate:.1f}% ({lang_fns}/{count})")
        
    stats = {
        "overall_fn_rate_pct": fn_rate,
        "sample_size": len(sample),
        "false_negatives": total_fns,
        "by_language": lang_rates
    }
    
    manifest._data["gate_fn_stats"] = stats
    manifest._flush()
    
    return stats
