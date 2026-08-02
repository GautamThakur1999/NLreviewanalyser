import re
import logging
from engine.store.verbatim import Verbatim

logger = logging.getLogger(__name__)

# Very broad keyword lists tuned for RECALL.
# We want to catch ANY review that might be talking about delivery, groceries, 
# quick commerce, competing apps, or specific category items.
# We also include Hindi/Hinglish terms.

CATEGORY_KEYWORDS = {
    # Competitors and brand names
    r"\b(blinkit|zepto|swiggy|instamart|zomato|dunzo|bbnow|bigbasket|amazon fresh)\b",
    # Core concepts
    r"\b(deliver|delivering|delivered|delivery|order|ordered|ordering|app|service|time|min|minutes)\b",
    # Hindi/Hinglish equivalents
    r"\b(samay|bhejo|aaya|aa gaya|mangwa|mangaya|pahucha|pahuncha|diya|de diya|karo)\b",
    # Grocery / Items
    r"\b(grocery|groceries|item|items|product|products|vegetable|vegetables|fruit|fruits|milk|bread|egg|eggs)\b",
    # Hindi items
    r"\b(sabzi|sabji|fal|doodh|anda)\b",
    # Pricing/Fees/Trials
    r"\b(price|cost|fee|fees|charge|charges|expensive|cheap|discount|offer|coupon|free|try|tried|first time)\b",
    # Hindi pricing
    r"\b(paisa|paise|sasta|mehanga|mahnga|loot)\b",
    # Missing/Bad
    r"\b(missing|bad|worst|good|great|best|fake|expired|rotten|refund|customer care|support)\b",
}

# Compile a single regex for speed
PREFILTER_REGEX = re.compile(
    "|" .join(CATEGORY_KEYWORDS),
    re.IGNORECASE
)

def applies_to_category(text: str) -> bool:
    """
    Zero-token heuristic check. 
    Returns True if the text contains any plausibly relevant keywords.
    Returns False if it seems completely unrelated (or is too short/generic).
    """
    if not text or not text.strip():
        return False
        
    # Extremely short reviews (e.g. "good", "nice app") often lack context but we might want them?
    # Let's say if it hits ANY of our broad keywords ("good", "app"), it passes.
    return bool(PREFILTER_REGEX.search(text))

def run_prefilter(verbatims: list[Verbatim]) -> tuple[list[Verbatim], list[Verbatim]]:
    """
    Splits verbatims into (passed, excluded).
    """
    passed = []
    excluded = []
    
    for v in verbatims:
        text = v.text_clean or v.text_original
        if applies_to_category(text):
            passed.append(v)
        else:
            excluded.append(v)
            
    logger.info(f"Prefilter: {len(passed)} passed, {len(excluded)} excluded ({(len(excluded)/len(verbatims))*100:.1f}%)")
    return passed, excluded
