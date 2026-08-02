"""
Insight Synthesis - Phase 5 (T-P5-04/05/06/07)
"""
import json
import logging
import re
from pathlib import Path

from engine.cluster.schema import ThemeCollection
from engine.synthesise.schema import Insight, InsightCollection
from engine.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

RESEARCH_QUESTIONS = [
    {"id": "rq1", "text": "Why do users repeat the same categories?"},
    {"id": "rq2", "text": "What prevents exploration of new categories?"},
    {"id": "rq3", "text": "How do users discover new products today?"},
    {"id": "rq4", "text": "What is the role of habit and timing in calcification?"},
    {"id": "rq5", "text": "What information is needed before trying?"},
    {"id": "rq6", "text": "What are recurring frustrations suppressing trust?"},
    {"id": "rq7", "text": "Which segments experiment the most?"},
    {"id": "rq8", "text": "Are there unmet needs or latent demand?"}
]

def synthesize_insights(
    themes: ThemeCollection,
    gemini_client: GeminiClient,
    model_id: str
) -> InsightCollection:
    """Answers 8 RQs using Themes. Applies scope lint and confidence rules."""
    
    # 1. Prepare evidence payload
    # For a real run we might filter relevant themes per RQ. For now, we provide top themes.
    top_themes = sorted(themes.themes, key=lambda t: t.mention_count, reverse=True)[:30]
    
    themes_str = []
    for t in top_themes:
        sources = list(t.distribution.source_counts.keys())
        themes_str.append(f"[{t.theme_id}] {t.name} (Mentions: {t.mention_count}, Sources: {sources})")
    
    evidence_block = "\n".join(themes_str)
    
    insights = []
    
    for rq in RESEARCH_QUESTIONS:
        logger.info(f"Synthesising Insight for RQ: {rq['text']}")
        
        # T-P5-07 Cannot-Answer Path
        # Determine if we have enough evidence for this RQ based on a heuristic floor.
        # e.g., if we only have < 3 total themes in the corpus, we abort early.
        if len(top_themes) < 3:
            logger.warning(f"Not enough evidence for {rq['id']}. Emitting cannot-answer.")
            insights.append(Insight(
                insight_id=f"insight_{rq['id']}",
                research_question_id=rq['id'],
                claim="Cannot be answered from this corpus.",
                mechanism="Insufficient data volume across sources to triangulate a finding.",
                segment="N/A",
                implication="Data gap must be closed before this can be answered.",
                confidence="low"
            ))
            continue
            
        sys_prompt = f"""You are a Lead User Researcher. 
Answer the Research Question using ONLY the provided Theme Evidence.
You must extract:
- claim: The core finding.
- mechanism: The underlying 'why'.
- segment: Who this affects.
- implication: The business impact.
- contradicting_evidence: Any conflicting themes (or null).

CRITICAL: Do NOT propose solutions or roadmaps in 'implication'. Just state the impact.
"""
        user_prompt = f"Research Question: {rq['text']}\n\n<EVIDENCE>\n{evidence_block}\n</EVIDENCE>"
        
        try:
            res = gemini_client.complete_structured(
                system=sys_prompt,
                user=user_prompt,
                schema=Insight
            )
            insight: Insight = res.parsed
            if not insight:
                continue
                
            insight.insight_id = f"insight_{rq['id']}"
            insight.research_question_id = rq['id']
            
            # T-P5-06 Scope Lint
            # Flag solution-oriented language
            solution_patterns = [r"we should", r"add a feature", r"build a", r"roadmap", r"launch"]
            for pat in solution_patterns:
                if re.search(pat, insight.implication, re.IGNORECASE):
                    logger.warning(f"Scope Lint Warning: Solution language detected in implication for {rq['id']}.")
                    insight.implication = f"[SCOPE WARNING] {insight.implication}"
                    break
                    
            # T-P5-05 Confidence computed in code
            # Check source diversity of supporting themes
            sources_triangulated = set()
            for theme_id in insight.supporting_theme_ids:
                t = next((x for x in themes.themes if x.theme_id == theme_id), None)
                if t:
                    sources_triangulated.update(t.distribution.source_counts.keys())
                    
            # If supported by only 1 source, cap at 'medium' regardless of LLM output
            if len(sources_triangulated) <= 1:
                logger.info(f"Confidence override for {rq['id']}: Capping to medium due to single-source evidence.")
                insight.confidence = "medium"
            
            insights.append(insight)
            
        except Exception as e:
            logger.error(f"Failed to synthesize {rq['id']}: {e}")
            
    return InsightCollection(insights=insights)
