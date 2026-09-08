"""
Integration tests for ChatSearchEngine retrieval, ranking, and context slicing.
"""

import pytest


def test_corpus_loaded_correctly(engine):
    assert len(engine.corpus) == 4250
    assert engine.embeddings is not None
    assert engine.embeddings.shape[0] == 4250
    assert len(engine.participant_map) > 0


def test_basic_search_returns_results(engine):
    res = engine.search("manali wooden cottage stay", top_k=5)
    assert "results" in res
    assert "query_analysis" in res
    assert len(res["results"]) > 0
    assert len(res["results"]) <= 5

    top_result = res["results"][0]
    assert "message" in top_result
    assert "score" in top_result
    assert "context" in top_result
    assert top_result["score"] > 0.0


def test_context_window_structure(engine):
    res = engine.search("wooden cottage booked in old manali", top_k=1, context_radius=3)
    results = res["results"]
    assert len(results) >= 1
    ctx = results[0]["context"]
    assert len(ctx) >= 1
    # Check that at least one item in context is marked as target
    has_target = any(c.get("is_target") for c in ctx)
    assert has_target is True


def test_attributed_speaker_search(engine):
    res = engine.search("what did Kabir say about the budget cap?", top_k=5)
    qa = res["query_analysis"]
    assert qa["sender_filter"] == "Kabir Sharma"
    assert qa["query_type"] == "attributed"
    # All retrieved messages should be from Kabir Sharma
    for r in res["results"]:
        assert r["message"]["sender"] == "Kabir Sharma"


def test_temporal_search(engine):
    res = engine.search("what happened in early September?", top_k=5)
    qa = res["query_analysis"]
    assert qa["date_start"] is not None
    assert qa["date_end"] is not None
    assert qa["query_type"] == "temporal"


def test_get_context_valid_and_invalid(engine):
    # Valid ID 840
    valid_res = engine.get_context(message_id=840, radius=3)
    assert "messages" in valid_res
    assert valid_res["target_message_id"] == 840
    assert any(m["id"] == 840 and m["is_target"] for m in valid_res["messages"])

    # Invalid ID
    invalid_res = engine.get_context(message_id=9999999, radius=3)
    assert "error" in invalid_res


def test_semantic_floor_suppresses_filler(engine):
    # Query for something highly specific and ensure scores are non-negative
    res = engine.search("FastAPI backend postgres models", top_k=5)
    for r in res["results"]:
        assert r["score"] > 0.0
