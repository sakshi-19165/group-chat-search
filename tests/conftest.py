"""
Shared pytest fixtures for the test suite.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.search import ChatSearchEngine
from server.app import app

CORPUS_PATH = os.path.join(PROJECT_ROOT, "dataset", "chat_corpus.json")
EMBEDDINGS_PATH = os.path.join(PROJECT_ROOT, "engine", "embeddings.npy")


@pytest.fixture(scope="session")
def engine():
    """Session-scoped singleton ChatSearchEngine."""
    return ChatSearchEngine(CORPUS_PATH, EMBEDDINGS_PATH)


@pytest.fixture(scope="session")
def client():
    """Session-scoped TestClient for API endpoints."""
    with TestClient(app) as test_client:
        yield test_client
