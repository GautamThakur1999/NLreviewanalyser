"""
T-P2-10 - Spam & bot filtering.

Detects URL spam, promotional/referral codes, and extreme repeating characters.
Hindi slang/expletives are NOT spam.
If flagged, returns a quarantine reason string, else None.

Guards: EC-D-06, EC-D-07
"""

import re

# Match extreme repeating characters (e.g., > 15 times)
# "soooooo good" (6 'o's) -> valid
# "soooooooooooooooo good" (16 'o's) -> spam
REPEATING_CHAR_RE = re.compile(r'(.)\1{15,}')

# Match promotional/referral patterns
# "use my code", "use code", "referral", "Rs 50 off" (Wait, Rs 50 off might be valid feedback, e.g. "I got Rs 50 off")
# Actually, users might say "They promised Rs 50 off but didn't give it".
# Let's target explicit referral/promo codes: "use my code X", "referral code", "invite code", "promo code X"
PROMO_CODE_RE = re.compile(
    r'(?i)\b(?:use (?:my )?(?:referral |promo )?code|referral code|invite code|sign up with code|download using code)\b'
)

# Match URLs
URL_RE = re.compile(
    r'(?i)\b(?:https?://|www\.)[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:[/?]\S+)?\b'
)

def check_spam(text: str) -> str | None:
    """
    Check if text contains spam. Returns quarantine reason if spam, else None.
    """
    if not text:
        return None
        
    if URL_RE.search(text):
        return "spam_bot_url"
        
    if PROMO_CODE_RE.search(text):
        return "spam_bot_promo"
        
    if REPEATING_CHAR_RE.search(text):
        return "spam_bot_repeating_chars"
        
    return None
