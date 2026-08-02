import pytest
import json
from pathlib import Path
from deploy.export import run_leak_check

def test_leak_check_passes_safe_data():
    safe_json = json.dumps({"theme": "price is too high", "frequency": 10})
    # Should not raise any exception
    run_leak_check(safe_json, "test_safe")

def test_leak_check_fails_on_email():
    unsafe_json = json.dumps({"theme": "price is high", "user": "test@example.com"})
    with pytest.raises(SystemExit) as excinfo:
        run_leak_check(unsafe_json, "test_email")
    assert excinfo.value.code == 1

def test_leak_check_fails_on_phone():
    unsafe_json = json.dumps({"theme": "delivery slow", "contact": "+12345678901"})
    with pytest.raises(SystemExit) as excinfo:
        run_leak_check(unsafe_json, "test_phone")
    assert excinfo.value.code == 1

def test_leak_check_fails_on_author_hash():
    unsafe_json = json.dumps({"theme": "app crash", "author_hash": "a1b2c3d4e5f6"})
    with pytest.raises(SystemExit) as excinfo:
        run_leak_check(unsafe_json, "test_author_hash")
    assert excinfo.value.code == 1

def test_leak_check_fails_on_url():
    unsafe_json = json.dumps({"theme": "app crash", "link": "https://example.com/profile/123"})
    with pytest.raises(SystemExit) as excinfo:
        run_leak_check(unsafe_json, "test_url")
    assert excinfo.value.code == 1
