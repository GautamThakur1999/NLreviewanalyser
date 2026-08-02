import pytest
from engine.clean.pii import redact_pii, check_for_pii, hash_author
from pathlib import Path

def test_indian_prices_protected():
    fixture_path = Path(__file__).parent / "fixtures" / "indian_prices.txt"
    text = fixture_path.read_text(encoding="utf-8")
    
    redacted = redact_pii(text)
    
    # Assert that no redactions were made
    assert "<PHONE>" not in redacted
    assert "<ORDER_ID>" not in redacted
    assert "<EMAIL>" not in redacted
    
    # Assert the original numbers are intact
    assert "₹500" in redacted
    assert "2kg" in redacted
    assert "500g" in redacted
    assert "Rs. 99" in redacted
    assert "1L" in redacted
    assert "50 rupees" in redacted
    assert "₹99 off" in redacted
    assert "$50" in redacted
    assert "€40" in redacted
    assert "Rs 1200" in redacted
    assert "15%" in redacted
    
    # And check_for_pii should be false
    assert not check_for_pii(text)

def test_pii_samples_redacted():
    fixture_path = Path(__file__).parent / "fixtures" / "pii_samples.txt"
    text = fixture_path.read_text(encoding="utf-8")
    
    redacted = redact_pii(text)
    
    # Assert PII was redacted
    assert "<PHONE>" in redacted
    assert "<EMAIL>" in redacted
    assert "<ORDER_ID>" in redacted
    
    # Specific assertions
    assert "9876543210" not in redacted
    assert "+91 99999-88888" not in redacted
    assert "098765 43210" not in redacted
    assert "test@example.com" not in redacted
    assert "OD1234567890" not in redacted
    assert "#123456789" not in redacted
    assert "110001" not in redacted
    assert "87654321" not in redacted
    
    # And check_for_pii should be true
    assert check_for_pii(text)

def test_hash_author():
    assert hash_author(None) is None
    h1 = hash_author("user123")
    h2 = hash_author("user123")
    assert h1 == h2
    assert h1 is not None
    assert len(h1) == 64  # sha256 hex
