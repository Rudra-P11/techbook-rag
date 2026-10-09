import pytest
from app.ingestion.cleaner import text_cleaner


def test_clean_hyphenation():
    dirty = "This is a trans-\nformer architecture for deep learning."
    cleaned = text_cleaner.clean(dirty)
    assert "transformer architecture" in cleaned


def test_clean_extra_whitespace():
    dirty = "Line 1\n\n\n\n\nLine 2"
    cleaned = text_cleaner.clean(dirty)
    assert cleaned == "Line 1\n\nLine 2"


def test_is_likely_scanned():
    assert text_cleaner.is_likely_scanned("   ") is True
    assert text_cleaner.is_likely_scanned("A very detailed paragraph with enough text to be native.") is False
