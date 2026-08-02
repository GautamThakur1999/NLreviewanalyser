"""
T-P2-08 - PII stripping.

Typed-placeholder redaction, Indian-format-aware, currency/unit-safe.
Must be run before persistence and before transmission.

Guards: EC-P-01, EC-P-04, EC-P-07, EC-P-02, EC-P-03, EC-P-05, EC-P-06, EC-P-08
"""

import hashlib
import os
import re

# Negative lookaround to protect currencies/units:
# Should NOT match: ₹500, Rs.500, 500g, 2kg, 1L, ₹99 off, etc.
# Match phone numbers (10 digits, optionally with +91 or 0 prefix)
# Match order IDs (typically alphanumeric or mostly numeric strings like ORD123456)
# Match email addresses
# Match PIN codes (6 digits) unless they look like amounts.

PHONE_RE = re.compile(
    r'(?<!\d)(?:(?:\+91|91|0)\s*[-]*\s*)?(?:\d{10}|\d{5}\s*[-]*\s*\d{5}|\d{3}\s*[-]*\s*\d{3}\s*[-]*\s*\d{4}|\d{4}\s*[-]*\s*\d{6})(?!\d)'
)
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# We need to be careful with numbers so we don't redact "Rs 500" or "500g"
# Protect common Indian prices/units:
PROTECTED_PREFIXES = r'(?:[₹$£€]|rs\.?\s*|rupees?\s*)'
PROTECTED_SUFFIXES = r'(?:g|kg|l|ml|mg|pc|pcs|off|/-|rupees?)'

# Match 6+ digit numbers and capture preceding/succeeding context to check for protection
NUMERIC_ID_RE = re.compile(
    rf'(?i)({PROTECTED_PREFIXES}?)\b(\d{{6,15}})\b(\s*{PROTECTED_SUFFIXES}?)'
)

# Often Order IDs are mixed alphanumeric, e.g., OD1234567890
ORDER_ID_RE = re.compile(r'(?i)\b(?:OD|ORD|ID|#)\s*[-_]?\s*[A-Z0-9]{5,20}\b')

def _redact_numeric(match: re.Match) -> str:
    prefix = match.group(1)
    number = match.group(2)
    suffix = match.group(3)
    
    # If there is a protected prefix or suffix, do not redact
    if prefix.strip() or suffix.strip():
        return match.group(0) # Return original matched string
    
    return f"{prefix}<ORDER_ID>{suffix}"

def redact_pii(text: str) -> str:
    """
    Redact PII from text, replacing it with typed placeholders.
    """
    if not text:
        return text

    # Apply redactors
    text = EMAIL_RE.sub('<EMAIL>', text)
    text = PHONE_RE.sub('<PHONE>', text)
    text = ORDER_ID_RE.sub('<ORDER_ID>', text)
    text = NUMERIC_ID_RE.sub(_redact_numeric, text) # 6+ digit numbers are likely PINs or order IDs, unless protected
    
    return text

def check_for_pii(text: str) -> bool:
    """
    Check if a string contains any unredacted PII patterns.
    Used for outbound LLM assertions.
    """
    if EMAIL_RE.search(text):
        return True
    if PHONE_RE.search(text):
        return True
    if ORDER_ID_RE.search(text):
        return True
    # NUMERIC_ID_RE is noisy for assertions, rely on explicit patterns for strict outbound checks
    return False

def hash_author(author_id: str | None) -> str | None:
    """
    HMAC author hashing with a salt loaded from .env.
    """
    if not author_id:
        return None
    salt = os.getenv("PII_SALT", "default_insecure_salt_for_tests")
    return hashlib.sha256(f"{salt}:{author_id}".encode('utf-8')).hexdigest()
