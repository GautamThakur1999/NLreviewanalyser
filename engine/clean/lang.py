"""
T-P2-12 - Language identification incl. Hinglish.

Simple heuristics:
1. Devanagari script presence -> 'hi'
2. Common Hinglish word presence -> 'hi-Latn'
3. Otherwise -> 'en'

Guards: EC-N-01
"""

import re
from engine.store.verbatim import Verbatim

# Devanagari Unicode block
DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')

# Common Hinglish words (lowercase)
HINGLISH_WORDS = {
    "hai", "bhai", "yaar", "accha", "thik", "mast", "bekar", "paise", 
    "kyu", "nahi", "ek", "se", "ko", "ki", "me", "kya", "toh", "ka", 
    "aur", "bhi", "yeh", "woh", "jo", "hum", "tum", "aap", "karo", "karna",
    "wala", "wali", "wale", "kuch", "koi", "sab", "ab", "kab", "jab", "tab",
    "sirf", "bilkul", "bahut", "bohot", "jyada", "kam", "mat", "kar", "de",
    "do", "le", "lo", "aaj", "kal", "abhi", "kabhi", "humesha"
}

def identify_language(text: str) -> str:
    """
    Identify language of the text.
    Returns one of: 'en', 'hi', 'hi-Latn'
    """
    if not text:
        return "en"
        
    # Check for Devanagari
    if DEVANAGARI_RE.search(text):
        return "hi"
        
    # Check for Hinglish
    tokens = set(re.findall(r'\b[a-z]+\b', text.lower()))
    hinglish_count = len(tokens.intersection(HINGLISH_WORDS))
    
    # If we find at least 2 common Hinglish words, consider it Hinglish
    # For very short texts, 1 might be enough if it's the main word.
    if hinglish_count >= 2 or (len(tokens) <= 3 and hinglish_count >= 1):
        return "hi-Latn"
        
    return "en"

def annotate_language(verbatims: list[Verbatim]) -> list[Verbatim]:
    annotated = []
    for v in verbatims:
        lang = identify_language(v.text_clean)
        annotated.append(v.model_copy(update={
            "lang": lang,
            "lang_confidence": 1.0,  # We are very confident in our simple heuristics!
            "is_romanised": (lang == "hi-Latn")
        }))
    return annotated
