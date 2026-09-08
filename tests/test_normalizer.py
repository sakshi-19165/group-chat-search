"""
Unit tests for the Hinglish semantic normalizer.
"""

import pytest
from engine.normalizer import normalize_text, clean_query_text, HINGLISH_DICT


def test_empty_and_whitespace():
    assert normalize_text("") == ""
    assert normalize_text(None) == ""
    assert clean_query_text("   ") == ""


def test_plain_english_passthrough():
    text = "Please submit your project before midnight"
    res = normalize_text(text)
    # Even if midnight or project matches, the original text is preserved in the output prefix
    assert res.startswith(text)


def test_hinglish_expansion_paisa():
    text = "Bhai paisa transfer kardo"
    res = normalize_text(text)
    assert "SEMANTIC_TAGS:" in res
    assert "money" in res.lower()
    assert "payment" in res.lower()


def test_hinglish_expansion_kiraya_chaunvan():
    text = "Indiranagar flat ka chaunvan kiraya hai"
    res = normalize_text(text)
    assert "SEMANTIC_TAGS:" in res
    assert "rent" in res.lower() or "54000" in res.lower() or "fifty four" in res.lower()


def test_clean_query_text():
    raw = "What about the trip?! @#$%  to Manali???"
    cleaned = clean_query_text(raw)
    assert "?!" not in cleaned
    assert "@#$%" not in cleaned
    assert "  " not in cleaned
    assert "Manali" in cleaned
