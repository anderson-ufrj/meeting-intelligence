"""Smoke test fixtures — lightweight API client with mock pipeline."""

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


@pytest.fixture(scope="module")
def smoke_pipeline():
    """A mock pipeline wired into the FastAPI app for smoke testing."""
    insights = MeetingInsights(
        meeting_title="Smoke Test Meeting",
        summary="A meeting for smoke testing purposes.",
    )
    sentiments = [
        SentimentResult(speaker="Alice", overall_sentiment="positive", confidence=0.85),
    ]
    processed = ProcessedMeeting(
        meeting_id="smoke_001",
        tier=TierClassification.ORDINARY,
        insights=insights,
        sentiments=sentiments,
        vector_id="ordinary_smoke_001",
        audit_log=[{"step": "smoke"}],
    )

    mock_pipe = MagicMock()
    mock_pipe.process.return_value = processed
    mock_pipe.search_meetings.return_value = [
        {
            "meeting_id": "smoke_001",
            "score": 0.9,
            "title": "Smoke Test Meeting",
            "tier": "ordinary",
            "content_preview": "Smoke test content...",
        }
    ]

    # Stores
    mock_ordinary = MagicMock()
    mock_ordinary.namespace = "ordinary"
    mock_ordinary.list_meetings.return_value = [
        {"meeting_id": "smoke_001", "title": "Smoke Test Meeting", "tier": "ordinary"}
    ]
    mock_ordinary.get_meeting.return_value = {
        "metadata": {"meeting_id": "smoke_001", "title": "Smoke Test Meeting"},
        "document": "Smoke test document content",
        "processed_meeting": processed.model_dump(mode="json"),
    }
    # Wire up mock Redis for stats/dedup (needs real key dispatch)
    meeting_data_json = json.dumps({
        "metadata": {"meeting_id": "smoke_001", "title": "Smoke Test Meeting", "processed_at": "2025-02-18T14:00:00"},
        "document": "Smoke test document content",
        "processed_meeting": processed.model_dump(mode="json"),
    })

    def ordinary_get(key):
        if key.startswith("transcript:"):
            return "Alice: Hello from smoke test"
        if key.startswith("meeting:"):
            return meeting_data_json
        return None

    mock_ordinary.r = MagicMock()
    mock_ordinary.r.get.side_effect = ordinary_get
    mock_ordinary.r.smembers.return_value = {"smoke_001"}
    mock_ordinary._index_key.return_value = "idx:ordinary"
    mock_ordinary._data_key.side_effect = lambda mid: f"meeting:ordinary:{mid}"

    mock_sensitive = MagicMock()
    mock_sensitive.namespace = "sensitive"
    mock_sensitive.r = MagicMock()
    mock_sensitive.r.smembers.return_value = set()
    mock_sensitive._index_key.return_value = "idx:sensitive"
    mock_sensitive._data_key.side_effect = lambda mid: f"meeting:sensitive:{mid}"

    mock_pipe.stores = {"ordinary": mock_ordinary, "sensitive": mock_sensitive}

    return mock_pipe


@pytest.fixture(scope="module")
def smoke_client(smoke_pipeline):
    """TestClient with injected mock pipeline."""
    import backend.api as api_module

    original = api_module.pipeline
    api_module.pipeline = smoke_pipeline

    client = TestClient(api_module.app, raise_server_exceptions=False)
    yield client

    api_module.pipeline = original
