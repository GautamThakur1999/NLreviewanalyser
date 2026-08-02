"""
T-P0-03 - Text normalisation.

The SINGLE function producing text_clean. Three S1 edge cases collapse here.
Every other module must call normalise_text(); no module may produce text_clean
any other way (ST-02, ST-03).

Guards: EC-X-01, EC-X-02, EC-X-04, EC-X-09, EC-N-04, EC-N-06
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata

# ---------------------------------------------------------------------------
# Zero-width and invisible characters that break offset calculations
# ---------------------------------------------------------------------------
_ZWJ_PATTERN = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f"   # zero-width joiners / non-joiners / marks
    r"\ufeff"                              # BOM
    r"\u00ad"                             # soft hyphen
    r"\u034f"                             # combining grapheme joiner
    r"\u2028\u2029]"                       # line / paragraph separators
)

# Repeated newlines -> normalise to at most two (preserve paragraph breaks)
_MULTI_NL_PATTERN = re.compile(r"\n{3,}")

# ---------------------------------------------------------------------------
# Mojibake detector - common UTF-8-read-as-Latin-1 sequences.
#
# When UTF-8 bytes are mistakenly decoded as Latin-1 (ISO-8859-1), each
# original byte maps 1:1 to the Unicode codepoint with the same value.
# So the "broken" key is the sequence of Unicode codepoints whose values
# match the original UTF-8 bytes.
#
# Example: UTF-8 for U+20B9 (RUPEE SIGN) is [0xE2, 0x82, 0xB9].
# Misread as Latin-1 that becomes the string: U+00E2 + U+0082 + U+00B9
# which renders in Latin-1-aware editors as: â\x82¹
# We key on that exact Unicode string and replace with the correct char.
# ---------------------------------------------------------------------------
_MOJIBAKE_MAP: dict[str, str] = {
    "\u00e2\u0080\u0099": "\u2019",   # right single quotation mark
    "\u00e2\u0080\u009c": "\u201c",   # left double quotation mark
    "\u00e2\u0080\u009d": "\u201d",   # right double quotation mark
    "\u00e2\u0080\u0093": "\u2013",   # en dash
    "\u00e2\u0080\u0094": "\u2014",   # em dash
    "\u00c3\u00a9": "\u00e9",         # e-acute
    "\u00c3\u00a8": "\u00e8",         # e-grave
    "\u00c3\u00a0": "\u00e0",         # a-grave
    "\u00c3\u00a2": "\u00e2",         # a-circumflex
    "\u00c3\u00ae": "\u00ee",         # i-circumflex
    "\u00c3\u00b4": "\u00f4",         # o-circumflex
    "\u00c3\u00bb": "\u00fb",         # u-circumflex
    "\u00c3\u00a7": "\u00e7",         # c-cedilla
    "\u00c3\u00ab": "\u00eb",         # e-diaeresis
    "\u00c3\u00af": "\u00ef",         # i-diaeresis
    "\u00c3\u00bc": "\u00fc",         # u-diaeresis
    "\u00c3\u00b1": "\u00f1",         # n-tilde
    "\u00e2\u0082\u00b9": "\u20b9",   # RUPEE SIGN - CRITICAL, must survive price-barrier detection
    "\u00e2\u0080\u00a2": "\u2022",   # bullet
    "\u00e2\u0080\u00a6": "\u2026",   # ellipsis
}


def _repair_mojibake(text: str) -> str:
    """Fix the most common UTF-8-read-as-Latin-1 sequences."""
    for broken, fixed in _MOJIBAKE_MAP.items():
        if broken in text:
            text = text.replace(broken, fixed)
    return text


def normalise_text(raw: str | None) -> str:
    """
    Produce a stable, canonical text_clean from any raw verbatim string.

    Pipeline (order matters):
    1. None / empty guard
    2. Mojibake repair
    3. HTML entity decode
    4. Unicode NFC normalisation
    5. Strip zero-width joiners and invisible marks
    6. CRLF / CR -> LF
    7. Collapse internal whitespace (tabs, nbsp, etc.) within lines
    8. Collapse 3+ consecutive newlines to 2
    9. Strip leading / trailing whitespace

    The result is idempotent: normalise_text(normalise_text(x)) == normalise_text(x).

    Guards: EC-X-01 (CRLF/encoding), EC-X-02 (UTF-8), EC-X-04 (whitespace),
            EC-X-09 (invisible chars), EC-N-04 (mojibake), EC-N-06 (HTML entities)
    """
    if not raw:
        return ""

    # 1. Mojibake repair (before entity decode)
    text = _repair_mojibake(raw)

    # 2. HTML entity decode (e.g. &amp; -> &, &#8217; -> right-quote, &nbsp; -> NBSP)
    text = html.unescape(text)

    # 3. Unicode NFC (compose decomposed sequences: NFD 'e + combining acute' -> NFC 'e-acute')
    text = unicodedata.normalize("NFC", text)

    # 4. Strip zero-width joiners and invisible marks (offset-stability, EC-X-09)
    text = _ZWJ_PATTERN.sub("", text)

    # 5. CRLF / CR -> LF (EC-X-01)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 6. Non-breaking / exotic spaces -> regular space; tabs -> space (keep \n)
    text = re.sub(r"[\t\f\u00a0\u202f\u205f]+", " ", text)

    # 7. Collapse horizontal whitespace runs within each line
    lines = text.split("\n")
    lines = [re.sub(r" {2,}", " ", line).strip() for line in lines]
    text = "\n".join(lines)

    # 8. Collapse 3+ consecutive blank lines to 2
    text = _MULTI_NL_PATTERN.sub("\n\n", text)

    # 9. Strip leading / trailing whitespace
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# Hashes - both built on text_clean, never on text_raw (ST-03)
# ---------------------------------------------------------------------------


def content_hash(text_clean: str) -> str:
    """
    SHA-256 hex digest of the canonical text. Used for exact deduplication.

    Always called on the output of normalise_text(), never on raw text (ST-03).
    """
    return hashlib.sha256(text_clean.encode("utf-8")).hexdigest()


def simhash(text_clean: str, bits: int = 64) -> int:
    """
    64-bit SimHash for near-duplicate detection (Hamming distance <= 3).

    Algorithm: for each token, compute its hash; combine bit-weighted vectors;
    threshold the final vector.

    Always called on the output of normalise_text() (ST-03).
    """
    if not text_clean:
        return 0

    tokens = text_clean.lower().split()
    if not tokens:
        return 0

    v = [0] * bits
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)  # noqa: S324
        for i in range(bits):
            bit = (h >> i) & 1
            v[i] += 1 if bit else -1

    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= 1 << i

    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    """Number of differing bits between two SimHash fingerprints."""
    return bin(a ^ b).count("1")


# ---------------------------------------------------------------------------
# Verbatim-ID helper (used by Verbatim schema in Phase 1)
# ---------------------------------------------------------------------------


def verbatim_id(source: str, source_id: str) -> str:
    """
    sha256(source + source_id)[:16] - deterministic, stable across re-collection.

    Defined here (rather than in the Verbatim model) so the normalise package is
    the single owner of all hashing logic.
    """
    raw = f"{source}:{source_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
