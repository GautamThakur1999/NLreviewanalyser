"""
T-P3 Phase 3 Runner

Orchestrates the entire Gate & Codebook Induction phase:
1. Loads clean verbatims from Parquet snapshots.
2. Runs the zero-token prefilter (T-P3-06).
3. Runs the LLM Groq Gate (T-P3-01).
4. Measures Gate FN Rate (T-P3-02).
5. Runs Open Coding induction (T-P3-03).
6. Clusters and generates v1.yaml Codebook (T-P3-04).
7. Runs the Residue Check falsification test (T-P3-05).
"""

import logging
from pathlib import Path
import duckdb
from datetime import datetime

from engine.config.settings import Settings
from engine.store.manifest import Manifest, make_run_id
from engine.store.verbatim import Verbatim
from engine.llm.groq_client import GroqClient
from engine.llm.gemini_client import GeminiClient

from engine.gate.prefilter import run_prefilter
from engine.gate.llm_gate import run_llm_gate
from engine.gate.evaluate import evaluate_gate_fns
from engine.induce.extract import extract_open_codes
from engine.induce.cluster import cluster_and_induce_codebook
from engine.induce.residue import run_residue_check

logger = logging.getLogger(__name__)

def load_clean_verbatims(data_dir: Path, snapshot_id: str) -> list[Verbatim]:
    """Loads all non-quarantined verbatims from a snapshot."""
    snap_dir = data_dir / "snapshots" / snapshot_id
    if not snap_dir.exists():
        # Fallback to current parquet if snapshot not passed
        snap_dir = data_dir / "parquet"
        
    con = duckdb.connect(database=':memory:')
    try:
        df = con.execute(f"SELECT * FROM read_parquet('{str(snap_dir)}/*/*/*.parquet') WHERE run_id NOT LIKE 'quarantine_%'").df()
    except Exception as e:
        logger.error(f"Failed to read parquet: {e}")
        return []
        
    verbatims = []
    # Convert DF back to Verbatim objects
    for _, row in df.iterrows():
        # Note: converting back from parquet requires careful handling of types.
        # For simplicity in this runner, we build a basic Verbatim.
        v_dict = row.to_dict()
        # Handle nan/NaT
        v_dict = {k: (v if not str(v) == 'nan' else None) for k, v in v_dict.items()}
        try:
            verbatims.append(Verbatim(**v_dict))
        except Exception as e:
            pass
    return verbatims

def run_phase3(settings: Settings, data_dir: Path, snapshot_id: str = ""):
    runs_dir = data_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id(runs_dir)
    manifest = Manifest(run_id, runs_dir / run_id / "manifest_p3.json")
    
    logger.info(f"Starting Phase 3 (Gate & Induction) Run: {run_id}")
    manifest.record_stage_start("phase3")
    
    groq_model = settings.llm.gate.model if settings.llm else "llama-3.3-70b-versatile"
    gemini_model = settings.llm.induce.model if settings.llm else "gemini-2.0-flash"
    
    groq_client = GroqClient(
        api_key=settings.groq_api_key,
        model=groq_model,
        rpm=settings.llm.gate.rpm if settings.llm else None,
        tpm=settings.llm.gate.tpm if settings.llm else None
    )
    groq_client_70b = GroqClient(
        api_key=settings.groq_api_key,
        model="llama-3.3-70b-versatile",
        rpm=30,
        tpm=131000,
    )
    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=gemini_model,
        rpm=settings.llm.induce.rpm if settings.llm else None,
        tpm=settings.llm.induce.tpm if settings.llm else None
    )
    
    # 1. Load data
    logger.info("Loading verbatims from Parquet...")
    all_verbatims = load_clean_verbatims(data_dir, snapshot_id)
    logger.info(f"Loaded {len(all_verbatims)} clean verbatims.")
    
    if not all_verbatims:
        logger.error("No verbatims found. Aborting Phase 3.")
        manifest.complete("failed")
        return
        
    # Cap size for the spike/demonstration so it doesn't burn too many tokens if corpus is huge
    max_corpus = 1000
    if len(all_verbatims) > max_corpus:
        import random
        random.seed(42)  # Seed to ensure we always pick the same 1000 items and hit our cache!
        all_verbatims = random.sample(all_verbatims, max_corpus)
        logger.info(f"Downsampled corpus to {max_corpus} for Phase 3 execution (seeded).")
        
    # 2. Prefilter
    passed_prefilter, excluded_prefilter = run_prefilter(all_verbatims)
    
    # 3. LLM Gate
    relevant, irrelevant_llm = run_llm_gate(passed_prefilter, groq_client, groq_model)
    
    # Combine excluded for FN check
    all_irrelevant = excluded_prefilter + irrelevant_llm
    
    # 4. FN Measurement
    fn_stats = evaluate_gate_fns(all_irrelevant, groq_client, groq_model, manifest, sample_size=30)
    
    # T-P3-03: Open Coding
    logger.info("--- PASS A: OPEN CODING ---")
    extractions = extract_open_codes(
        relevant_verbatims=relevant,
        client=groq_client,
        model_id=groq_model,
        sample_size=120
    )
    
    # T-P3-04: Construct Codebook v1
    logger.info("--- BUILDING CODEBOOK v1 ---")
    codebook_dir = Path(data_dir) / "codebooks"
    codebook_path = cluster_and_induce_codebook(extractions, groq_client, groq_model, codebook_dir)
    
    # 7. Residue Check (Pass B)
    residue_stats = run_residue_check(relevant, groq_client, groq_model, codebook_path, manifest, sample_size=30)
    
    manifest.complete("success")
    logger.info("Phase 3 complete.")
    
if __name__ == "__main__":
    from engine.config.settings import get_settings
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    settings = get_settings()
    data_dir = Path("data")
    run_phase3(settings, data_dir)
