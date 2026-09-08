"""
Unit tests for fuzzy natural language temporal expressions parser.
"""

import pytest
from datetime import datetime
from engine.search import ChatSearchEngine


def test_specific_date(engine):
    start, end = engine.parse_fuzzy_temporal("what happened on june 15", year=2024)
    assert start is not None and end is not None
    assert start.month == 6 and (start.day <= 15)
    assert end.month == 6 and (end.day >= 15)


def test_early_month(engine):
    start, end = engine.parse_fuzzy_temporal("early september plans", year=2024)
    assert start is not None and end is not None
    assert start.month in [8, 9]
    assert end.month == 9 and end.day == 10


def test_mid_month(engine):
    start, end = engine.parse_fuzzy_temporal("discussions in mid-october", year=2024)
    assert start is not None and end is not None
    assert start.month == 10 and start.day == 8
    assert end.month == 10 and end.day == 22


def test_late_month(engine):
    start, end = engine.parse_fuzzy_temporal("late october submission", year=2024)
    assert start is not None and end is not None
    assert start.month == 10 and start.day == 20
    assert end.month == 11 or (end.month == 10 and end.day >= 30)


def test_cultural_landmark_independence_day(engine):
    start, end = engine.parse_fuzzy_temporal("messages around independence day", year=2024)
    assert start is not None and end is not None
    assert start.month == 8 and start.day == 8
    assert end.month == 8 and end.day == 20


def test_no_temporal_expression(engine):
    start, end = engine.parse_fuzzy_temporal("who booked the wooden cottage", year=2024)
    assert start is None
    assert end is None
