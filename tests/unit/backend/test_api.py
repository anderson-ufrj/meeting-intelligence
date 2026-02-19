"""Tests for FastAPI endpoints (Phase 4)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.models import (
    MeetingInsights,
    ProcessedMeeting,
    SentimentResult,
    TierClassification,
)


@pytest.fixture
def mock_pipeline_for_api(sample_insights, sample_sentiments):
    """Create a mock pipeline suitable for API testing."""
    mock_pipe = MagicMock()

    # Process returns a ProcessedMeeting
    processed = ProcessedMeeting(
        meeting_id="meeting_abc123",
        tier=TierClassification.ORDINARY,
        insights=sample_insights,
        sentiments=sample_sentiments,
        vector_id="ordinary_abc123",
        audit_log=[{"step": "test"}],
    )
    mock_pipe.process.return_value = processed

    # Stores
    mock_ordinary_store = MagicMock()
    mock_sensitive_store = MagicMock()
    mock_ordinary_store.namespace = "ordinary"
    mock_sensitive_store.namespace = "sensitive"

    mock_pipe.stores = {
        "ordinary": mock_ordinary_store,
        "sensitive": mock_sensitive_store,
    }

    # Search
    mock_pipe.search_meetings.return_value = [
        {
            "meeting_id": "m1",
            "score": 0.92,
            "title": "Sprint Review",
            "tier": "ordinary",
            "content_preview": "Sprint review discussion...",
        }
    ]

    return mock_pipe, mock_ordinary_store, mock_sensitive_store


@pytest.fixture
def client(mock_pipeline_for_api):
    """Create a TestClient with the pipeline already injected."""
    mock_pipe, _, _ = mock_pipeline_for_api

    import backend.api as api_module
    # Inject mock pipeline
    original_pipeline = api_module.pipeline
    api_module.pipeline = mock_pipe

    # Create app without lifespan (avoids real pipeline init)
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    client = TestClient(api_module.app, raise_server_exceptions=False)
    yield client, mock_pipe, mock_pipeline_for_api[1], mock_pipeline_for_api[2]

    # Restore
    api_module.pipeline = original_pipeline


class TestHealth:
    def test_redis_connected(self):
        with patch("backend.api.redis.from_url") as mock_redis, \
             patch("backend.api.os.getenv", return_value="redis://fake:6379"):
            mock_r = MagicMock()
            mock_r.ping.return_value = True
            mock_redis.return_value = mock_r

            import backend.api as api_module
            original = api_module.pipeline
            api_module.pipeline = MagicMock()

            client = TestClient(api_module.app, raise_server_exceptions=False)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis"] == "connected"

            api_module.pipeline = original

    def test_redis_disconnected(self):
        with patch("backend.api.redis.from_url") as mock_redis:
            mock_redis.return_value.ping.side_effect = Exception("Connection refused")

            import backend.api as api_module
            original = api_module.pipeline
            api_module.pipeline = MagicMock()

            client = TestClient(api_module.app, raise_server_exceptions=False)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["redis"] == "disconnected"

            api_module.pipeline = original


class TestProcessMeeting:
    def test_success(self, client):
        test_client, mock_pipe, ordinary_store, _ = client
        ordinary_store.r = MagicMock()

        response = test_client.post("/api/v1/meetings/process", json={
            "title": "Sprint Review",
            "transcript": "Alice: Let's review the sprint goals and progress.",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert "meeting_id" in data
        assert "insights" in data
        assert "sentiments" in data

    def test_auto_generates_meeting_id(self, client):
        test_client, mock_pipe, ordinary_store, _ = client
        ordinary_store.r = MagicMock()

        response = test_client.post("/api/v1/meetings/process", json={
            "title": "Test Meeting",
            "transcript": "Alice: Hello everyone, let's get started.",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"].startswith("meeting_")

    def test_short_transcript_rejected(self, client):
        test_client, *_ = client

        response = test_client.post("/api/v1/meetings/process", json={
            "title": "Test",
            "transcript": "Short",
        })

        assert response.status_code == 422

    def test_invalid_tier_rejected(self, client):
        test_client, *_ = client

        response = test_client.post("/api/v1/meetings/process", json={
            "title": "Test",
            "tier": "invalid_tier",
            "transcript": "This is a sufficiently long transcript for testing.",
        })

        assert response.status_code == 422

    def test_pipeline_not_ready(self):
        import backend.api as api_module
        original = api_module.pipeline
        api_module.pipeline = None

        test_client = TestClient(api_module.app, raise_server_exceptions=False)
        response = test_client.post("/api/v1/meetings/process", json={
            "title": "Test",
            "transcript": "This is a sufficiently long transcript for testing.",
        })

        assert response.status_code == 503
        api_module.pipeline = original


class TestListMeetings:
    def test_returns_meetings(self, client):
        test_client, _, ordinary_store, _ = client
        ordinary_store.list_meetings.return_value = [
            {"meeting_id": "m1", "title": "Sprint Review"},
            {"meeting_id": "m2", "title": "Standup"},
        ]

        response = test_client.get("/api/v1/meetings?tier=ordinary")

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "ordinary"
        assert len(data["meetings"]) == 2


class TestGetMeeting:
    def test_found(self, client):
        test_client, _, ordinary_store, _ = client
        ordinary_store.get_meeting.return_value = {
            "metadata": {"meeting_id": "m1"},
            "document": "Sprint review content",
        }

        response = test_client.get("/api/v1/meetings/m1?tier=ordinary")

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["meeting_id"] == "m1"

    def test_not_found(self, client):
        test_client, _, ordinary_store, _ = client
        ordinary_store.get_meeting.return_value = None

        response = test_client.get("/api/v1/meetings/nonexistent?tier=ordinary")

        assert response.status_code == 404


class TestGetTranscript:
    def test_found(self, client):
        test_client, _, ordinary_store, _ = client
        ordinary_store.r = MagicMock()
        ordinary_store.r.get.return_value = "Alice: Hello\nBob: Hi"

        response = test_client.get("/api/v1/meetings/m1/transcript?tier=ordinary")

        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == "m1"
        assert "Alice: Hello" in data["transcript"]

    def test_not_found(self, client):
        test_client, _, ordinary_store, _ = client
        ordinary_store.r = MagicMock()
        ordinary_store.r.get.return_value = None

        response = test_client.get("/api/v1/meetings/m1/transcript?tier=ordinary")

        assert response.status_code == 404


class TestSearchMeetings:
    def test_returns_results(self, client):
        test_client, mock_pipe, _, _ = client

        response = test_client.get("/api/v1/meetings/search?q=sprint")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "sprint"
        assert len(data["results"]) == 1


class TestDeleteMeeting:
    def test_success(self, client):
        test_client, _, ordinary_store, _ = client

        response = test_client.delete("/api/v1/meetings/m1?tier=ordinary")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["meeting_id"] == "m1"
        ordinary_store.delete_meeting.assert_called_once_with("m1")


class TestStats:
    def test_empty(self, client):
        test_client, _, ordinary_store, sensitive_store = client
        ordinary_store.r = MagicMock()
        ordinary_store.r.smembers.return_value = set()
        ordinary_store._index_key.return_value = "idx:ordinary"
        sensitive_store.r = MagicMock()
        sensitive_store.r.smembers.return_value = set()
        sensitive_store._index_key.return_value = "idx:sensitive"

        response = test_client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_meetings"] == 0
