"""
API endpoint tests using FastAPI TestClient.
"""

import pytest


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["corpus_loaded"] == 4250
    assert data["embeddings_ready"] is True


def test_stats_endpoint(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 4250
    assert "start_date" in data
    assert "end_date" in data
    assert "participant_counts" in data
    assert len(data["participant_counts"]) >= 8
    assert "major_threads" in data


def test_search_endpoint_success(client):
    payload = {
        "query": "Who is driving the Scorpio to Manali?",
        "top_k": 5,
        "context_radius": 3
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert "query_analysis" in data


def test_search_endpoint_empty_query(client):
    response = client.post("/api/search", json={"query": "   "})
    assert response.status_code == 400
    assert "Query cannot be empty" in response.json()["detail"]


def test_context_endpoint_200(client):
    response = client.get("/api/context/840?radius=3")
    assert response.status_code == 200
    data = response.json()
    assert data["target_message_id"] == 840
    assert "messages" in data
    assert len(data["messages"]) > 0


def test_context_endpoint_404(client):
    response = client.get("/api/context/999999")
    assert response.status_code == 404


def test_chat_endpoint_empty_query(client):
    response = client.post("/api/chat", json={"query": ""})
    assert response.status_code == 400


def test_chat_endpoint_with_query(client):
    payload = {"query": "How much was the flat security deposit?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "cited_messages" in data


def test_benchmark_endpoint(client):
    response = client.get("/api/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "queries" in data
    metrics = data["metrics"]
    assert metrics["total_queries"] == 40
    assert metrics["hit_at_3"] >= 95.0
