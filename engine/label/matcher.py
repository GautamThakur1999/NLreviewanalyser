"""
T-P4-07 - Evidence-span recomputation
T-P4-08 - Matcher strictness test-lock

Recomputes the start/end offsets of a quote in the original verbatim text.
Discards the LLM's provided offsets to prevent drift on multi-byte text.
Fails closed if the quote is ungrounded (hallucinated).
"""

import re
from typing import Tuple

def normalize_whitespace(text: str) -> str:
    """Collapses multiple spaces/newlines into a single space."""
    return re.sub(r'\s+', ' ', text).strip()

def recompute_span(original_text: str, quote: str) -> Tuple[bool, int | None, int | None]:
    """
    Finds the exact start/end offsets of `quote` in `original_text`.
    
    1. Tries exact substring match.
    2. If fails, tries a whitespace-normalized match.
    3. If fails, returns (False, None, None) -> ungrounded hallucination.
    
    Returns:
        (is_grounded, start_idx, end_idx)
    """
    if not quote or not quote.strip():
        # If quote is empty, consider it ungrounded for evidence purposes.
        return False, None, None

    # Pass 1: Exact match
    start_idx = original_text.find(quote)
    if start_idx != -1:
        return True, start_idx, start_idx + len(quote)

    # Pass 2: Whitespace-normalized match
    # Since the original text has whitespace, we need to find the actual offsets.
    # We construct a regex from the normalized quote that matches variable whitespace.
    norm_quote = normalize_whitespace(quote)
    if not norm_quote:
        return False, None, None

    # Escape regex specials, then replace single spaces with \s+
    escaped_words = [re.escape(w) for w in norm_quote.split(' ')]
    regex_pattern = r'\s+'.join(escaped_words)
    
    try:
        match = re.search(regex_pattern, original_text)
        if match:
            return True, match.start(), match.end()
    except re.error:
        pass

    # Pass 3: Punctuation-stripped match
    # Strip all non-alphanumeric chars (except spaces) and regex match
    def strip_punc(s: str) -> str:
        return re.sub(r'[^\w\s]', '', s)
        
    stripped_quote = strip_punc(norm_quote)
    if stripped_quote:
        escaped_words_3 = [re.escape(w) for w in stripped_quote.split(' ')]
        # We need to match the words in the original text, allowing for any punctuation/whitespace between them
        regex_pattern_3 = r'[\s\W]+'.join(escaped_words_3)
        try:
            match = re.search(regex_pattern_3, original_text, re.IGNORECASE)
            if match:
                return True, match.start(), match.end()
        except re.error:
            pass

    # Pass 4: Fail closed. Do not attempt fuzzy or semantic matching.
    return False, None, None
