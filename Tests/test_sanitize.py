
from extractor import validate_and_sanitize_url
import pytest

def test_valid_url():
    assert validate_and_sanitize_url("https://example.com")

def test_invalid_scheme():
    with pytest.raises(ValueError):
        validate_and_sanitize_url("ftp://malicious.com")

def test_internal_ip():
    with pytest.raises(ValueError):
        validate_and_sanitize_url("http://127.0.0.1")
