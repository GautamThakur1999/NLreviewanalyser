"""
T-P4-09 - Full-corpus labelling run
T-P4-13 - Budget-forced stratified sampling

Runs Phase 4 labeling using the Codebook v1.
"""

import json
import logging
import random
from pathlib import Path
import yaml
import time
from typing import Tuple

from engine.config.settings import Settings
from engine.store.manifest import Manifest, make_run_id
from engine.store.verbatim import Verbatim
from engine.llm.groq_client import GroqClient
from engine.llm.prompts import build_prompt, VerbatimEntry

from engine.induce.runner import load_clean_verbatims
from engine.gate.prefilter import run_prefilter
from engine.gate.llm_gate import run_llm_gate

from engine.label.schema import BatchLabel, Label
from engine.label.matcher import recompute_span

logger = logging.getLogger(__name__)

def load_codebook(codebook_path: Path) -> dict:
    with open(codebook_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_label_prompt(codebook: dict) -> str:
    codes_str = json.dumps(codebook["codes"], indent=2)
    schema_str = json.dumps(BatchLabel.model_json_schema(), indent=2)
    return f"""You are an expert qualitative researcher.
Your task is to label user reviews based on the provided Codebook.

<CODEBOOK>
{codes_str}
</CODEBOOK>

For each verbatim in the DATA block:
1. Extract exact quotes that justify any of the codes from the Codebook.
2. Assign the relevant code and its barrier_type.
3. Also determine the overall sentiment.
4. Output your response as a valid JSON matching the schema precisely.

<EXPECTED_SCHEMA>
{schema_str}
</EXPECTED_SCHEMA>

CRITICAL:
Your output MUST be a valid JSON object matching the EXPECTED_SCHEMA precisely.
The root key must be `labels`.
The `quote` MUST be an EXACT substring of the verbatim's text_clean. Do not paraphrase.
If no codes apply, return an empty assigned_codes list.
"""

def stratify_sample(verbatims: list[Verbatim], budget: int) -> list[Verbatim]:
    """T-P4-13: Budget-forced stratified sampling."""
    if len(verbatims) <= budget:
        return verbatims
        
    # Group by source and brand
    strata = {}
    for v in verbatims:
        key = f"{v.source}_{v.brand}"
        strata.setdefault(key, []).append(v)
        
    sampled = []
    # Simple proportional allocation
    for key, items in strata.items():
        proportion = len(items) / len(verbatims)
        stratum_budget = max(1, int(budget * proportion))
        # Random sample with fixed seed for reproducible tracking
        random.seed(42 + len(items))
        sampled.extend(random.sample(items, min(stratum_budget, len(items))))
        
    return sampled

def label_batch(
    verbatims: list[Verbatim],
    client: GroqClient,
    model_id: str,
    codebook_version: str,
    prompt_str: str,
    run_id: str
) -> list[Label]:
    """Labels a small batch of verbatims and recomputes evidence spans."""
    
    entries = [
        VerbatimEntry(
            verbatim_id=v.verbatim_id,
            text_clean=v.text_clean,
            source=v.source,
            lang=v.lang
        ) for v in verbatims
    ]
    
    system, user = build_prompt(prompt_str, entries)
    
    try:
        res = client.complete_structured(
            system=system,
            user=user,
            schema=BatchLabel
        )
    except Exception as e:
        logger.warning(f"Batch label failed: {e}")
        return []
        
    if not res.parsed or not hasattr(res.parsed, "labels"):
        return []
        
    labels = []
    for llm_lbl in res.parsed.labels:
        # Match back to verbatim
        verb = next((v for v in verbatims if v.verbatim_id == llm_lbl.verbatim_id), None)
        if not verb:
            continue
            
        # T-P4-07 Evidence Span Recomputation
        for assigned in llm_lbl.assigned_codes:
            for span in assigned.evidence:
                is_grounded, start, end = recompute_span(verb.text_clean, span.quote)
                span.start = start
                span.end = end
                span.is_grounded = is_grounded
                if not is_grounded:
                    logger.debug(f"Hallucinated quote rejected: '{span.quote}'")
                    
        llm_lbl.provider = "groq"
        llm_lbl.model = model_id
        llm_lbl.codebook_version = codebook_version
        llm_lbl.run_id = run_id
        labels.append(llm_lbl)
        
    return labels

def run_phase4(settings: Settings, data_dir: Path, snapshot_id: str = ""):
    runs_dir = data_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    manifest = Manifest(run_id, runs_dir / run_id / "manifest_p4.json")
    
    logger.info(f"Starting Phase 4 (Labelling) Run: {run_id}")
    manifest.record_stage_start("phase4")
    
    codebook_path = data_dir / "codebooks" / "v1.yaml"
    if not codebook_path.exists():
        logger.error("Codebook v1.yaml not found! Run Phase 3 first.")
        return
        
    codebook = load_codebook(codebook_path)
    prompt_str = build_label_prompt(codebook)
    
    # 1. Load all data
    logger.info("Loading verbatims...")
    all_verbatims = load_clean_verbatims(data_dir, snapshot_id)
    
    # 2. T-P4-13 Budget-forced Sampling (Limit to 500 to save time/cost safely)
    BUDGET = 500
    sampled_verbatims = stratify_sample(all_verbatims, BUDGET)
    logger.info(f"Stratified sample drawn: {len(sampled_verbatims)} docs from corpus of {len(all_verbatims)}")
    
    # 3. Gate
    passed_prefilter, _ = run_prefilter(sampled_verbatims)
    
    # If someone reverts to Gemini, use correct TPM (32k)
    # gemini_model = "gemini-2.0-flash"
    # gemini_client = GeminiClient(
    #     api_key=settings.gemini_api_key,
    #     model=gemini_model,
    #     rpm=15,
    #     tpm=32000
    # )
    
    groq_model = "llama-3.1-8b-instant"
    groq_client = GroqClient(
        api_key=settings.groq_api_key,
        model=groq_model,
        rpm=30,
        tpm=6000
    )
    
    relevant, _ = run_llm_gate(passed_prefilter, groq_client, groq_model)
    logger.info(f"Docs passing LLM Gate: {len(relevant)}")
    
    # 4. Labelling
    BATCH_SIZE = 5
    final_labels = []
    
    logger.info("--- PASS B: MULTI-LABEL EXTRACTION ---")
    for i in range(0, len(relevant), BATCH_SIZE):
        batch = relevant[i:i+BATCH_SIZE]
        logger.info(f"Labelling batch {i}-{i+len(batch)} of {len(relevant)}...")
        
        batch_labels = label_batch(batch, groq_client, groq_model, "v1", prompt_str, run_id)
        final_labels.extend(batch_labels)
        
        # Free-tier rate limiting backoff
        time.sleep(2)
        
    # Save output
    labels_dir = data_dir / "labels" / run_id
    labels_dir.mkdir(parents=True, exist_ok=True)
    out_file = labels_dir / "labels.jsonl"
    
    with open(out_file, "w", encoding="utf-8") as f:
        for lbl in final_labels:
            f.write(lbl.model_dump_json() + "\n")
            
    logger.info(f"Saved {len(final_labels)} labels to {out_file}")
    manifest.complete("success")
    logger.info("Phase 4 complete.")

if __name__ == "__main__":
    from engine.config.settings import get_settings
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    s = get_settings()
    d = Path("data")
    run_phase4(s, d)
