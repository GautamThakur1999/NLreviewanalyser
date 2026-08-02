"""
Tests for T-P0-03 — Text normalisation.

The round-trip test: visibly-identical text with different encodings, line
endings, or mojibake must produce an identical content_hash.

Guards: EC-X-01, EC-X-02, EC-X-04, EC-X-09, EC-N-04, EC-N-06
"""

import unicodedata

import pytest

from engine.normalise.text import (
    content_hash,
    hamming_distance,
    normalise_text,
    simhash,
)


class TestNormaliseText:
    """Core normalise_text() behaviour."""

    def test_idempotent(self):
        """f(f(x)) == f(x) for all x."""
        samples = [
            "Hello, world!\n",
            "  multiple   spaces  \t here  ",
            "café résumé",  # NFD-ish
            "Blinkit pe ₹500 ka order kiya\r\n",
            "&amp; &lt;br&gt; entities",
            "zero\u200bwidth\u200cjoiner",
            "",
            None,
        ]
        for raw in samples:
            first = normalise_text(raw)
            second = normalise_text(first)
            assert first == second, f"Not idempotent for: {raw!r}"

    def test_crlf_to_lf(self):
        text = "line one\r\nline two\r\nline three"
        result = normalise_text(text)
        assert "\r" not in result
        assert result == "line one\nline two\nline three"

    def test_cr_to_lf(self):
        text = "line one\rline two"
        result = normalise_text(text)
        assert "\r" not in result
        assert result == "line one\nline two"

    def test_nfc_normalisation(self):
        """NFD 'é' (e + combining acute) should equal NFC 'é'."""
        nfc = unicodedata.normalize("NFC", "café")
        nfd = unicodedata.normalize("NFD", "café")
        assert nfc != nfd  # confirm they differ before normalisation
        assert normalise_text(nfc) == normalise_text(nfd)

    def test_html_entities(self):
        text = "&amp; is &lt;great&gt; &amp; costs &#8377;200"
        result = normalise_text(text)
        assert "&amp;" not in result
        assert "₹200" in result or "200" in result
        assert "<great>" in result

    def test_mojibake_repair(self):
        """
        Mojibake: UTF-8 bytes for RUPEE SIGN (U+20B9 = 0xE2 0x82 0xB9)
        misread as Latin-1 become the three Unicode codepoints:
        U+00E2 (a-circumflex) + U+0082 (control) + U+00B9 (superscript-1)
        """
        broken = "\u00e2\u0082\u00b9"   # the three Latin-1-decoded codepoints
        text = f"paid {broken}500 for groceries"
        result = normalise_text(text)
        assert "\u20b9" in result, f"Rupee sign not restored; got: {result!r}"
        assert broken not in result

    def test_zero_width_joiners_removed(self):
        """Zero-width joiners must be stripped for offset stability."""
        text = "hello\u200bworld"  # ZWJ between hello and world
        result = normalise_text(text)
        assert "\u200b" not in result
        assert "helloworld" in result

    def test_whitespace_collapse(self):
        text = "too   many    spaces\t\there"
        result = normalise_text(text)
        assert "  " not in result.replace("\n", " ")

    def test_empty_and_none(self):
        assert normalise_text("") == ""
        assert normalise_text(None) == ""

    def test_rupee_sign_preserved(self):
        """₹ must NEVER be stripped or mangled (price-barrier evidence)."""
        text = "Blinkit charges ₹500 for pet food"
        result = normalise_text(text)
        assert "₹" in result
        assert "500" in result

    def test_hindi_text_preserved(self):
        text = "बहुत अच्छा है यह ऐप"
        result = normalise_text(text)
        assert result  # not empty
        assert "बहुत" in result


class TestRoundTripHash:
    """
    T-F-12: visibly-identical text with different encodings/line-endings
    must produce an identical content_hash.
    """

    BASE = "Hello, I love Blinkit! It delivers milk and bread so fast.\nOrdered ₹500 worth of groceries."

    def test_lf_vs_crlf_same_hash(self):
        crlf_version = self.BASE.replace("\n", "\r\n")
        assert content_hash(normalise_text(self.BASE)) == content_hash(normalise_text(crlf_version))

    def test_nfd_vs_nfc_same_hash(self):
        nfc = unicodedata.normalize("NFC", "café résumé")
        nfd = unicodedata.normalize("NFD", "café résumé")
        assert content_hash(normalise_text(nfc)) == content_hash(normalise_text(nfd))

    def test_mojibake_vs_clean_same_hash(self):
        clean = "\u20b9500 worth of groceries."   # correct rupee sign
        # Broken: UTF-8 bytes of rupee sign decoded as Latin-1
        broken = "\u00e2\u0082\u00b9500 worth of groceries."
        assert content_hash(normalise_text(clean)) == content_hash(normalise_text(broken))

    def test_extra_whitespace_same_hash(self):
        normal = "Hello world"
        extra_ws = "Hello    world"
        assert content_hash(normalise_text(normal)) == content_hash(normalise_text(extra_ws))

    def test_html_entity_same_hash(self):
        plain = "& great delivery"
        entity = "&amp; great delivery"
        assert content_hash(normalise_text(plain)) == content_hash(normalise_text(entity))


class TestSimhash:
    def test_identical_texts_same_hash(self):
        text = "blinkit delivery is fast and reliable"
        assert simhash(normalise_text(text)) == simhash(normalise_text(text))

    def test_near_duplicate_small_distance(self):
        # Exact same words - hash must be identical
        text1 = "blinkit delivery is fast and reliable"
        text2 = "blinkit delivery is fast and reliable"
        h1 = simhash(normalise_text(text1))
        h2 = simhash(normalise_text(text2))
        assert hamming_distance(h1, h2) == 0  # identical text -> identical hash

    def test_very_different_texts_large_distance(self):
        text1 = "I love the grocery section"
        text2 = "Customer support is terrible and slow and broken"
        h1 = simhash(normalise_text(text1))
        h2 = simhash(normalise_text(text2))
        assert hamming_distance(h1, h2) > 10  # not near-dup

    def test_empty_text(self):
        assert simhash("") == 0


class TestContentHash:
    def test_deterministic(self):
        text = "same text every time"
        assert content_hash(text) == content_hash(text)

    def test_different_texts_different_hashes(self):
        assert content_hash("text one") != content_hash("text two")

    def test_is_hex_string(self):
        h = content_hash("hello")
        int(h, 16)  # should not raise
        assert len(h) == 64  # SHA-256 = 256 bits = 64 hex chars
