"""E2E tests — full pipeline flow with fakeredis, mock LLM, mock BERT."""

from datetime import datetime
from unittest.mock import patch

import pytest

from backend.models import (
    DialogueTurn,
    MeetingTranscript,
    ProcessedMeeting,
    Speaker,
    TierClassification,
)

pytestmark = pytest.mark.e2e


SAMPLE_TURNS = [
    DialogueTurn(timestamp="00:00:15", speaker="Alice Johnson", text="Let's review the sprint goals for this quarter."),
    DialogueTurn(timestamp="00:01:30", speaker="Bob Smith", text="I finished the API refactoring. All tests are green."),
    DialogueTurn(timestamp="00:02:45", speaker="Carol Davis", text="The new mockups are ready. I'll share them after the meeting."),
    DialogueTurn(timestamp="00:04:00", speaker="Alice Johnson", text="Great progress. Let's decide on the deployment date."),
    DialogueTurn(timestamp="00:05:10", speaker="Bob Smith", text="I suggest we deploy next Friday after QA approval."),
    DialogueTurn(timestamp="00:06:20", speaker="Alice Johnson", text="Agreed. Bob, can you write the deployment runbook by Thursday?"),
]

SAMPLE_SPEAKERS = [
    Speaker(name="Alice Johnson", email="alice@stormgeo.com", role="PM"),
    Speaker(name="Bob Smith", email="bob@stormgeo.com", role="Engineer"),
    Speaker(name="Carol Davis", role="Designer"),
]


class TestOrdinaryPipelineE2E:
    """Full flow: process ordinary transcript -> store -> search -> retrieve -> delete."""

    def test_process_and_store(self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_embedding):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url)

        transcript = MeetingTranscript(
            meeting_id="e2e_ordinary_001",
            title="Sprint Planning Q1",
            date=datetime(2025, 2, 18, 14, 0),
            tier=TierClassification.ORDINARY,
            participants=SAMPLE_SPEAKERS,
            turns=SAMPLE_TURNS,
        )

        result = pipeline.process(transcript)

        assert isinstance(result, ProcessedMeeting)
        assert result.meeting_id == "e2e_ordinary_001"
        assert result.tier == TierClassification.ORDINARY
        assert result.insights.meeting_title == "Sprint Planning Q1"
        assert len(result.insights.decisions) == 2
        assert len(result.insights.action_items) == 2
        assert len(result.sentiments) == 3  # Alice, Bob, Carol
        assert result.vector_id is not None

    def test_retrieve_stored_meeting(self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_embedding):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url)

        transcript = MeetingTranscript(
            meeting_id="e2e_retrieve_001",
            title="Retrieve Test",
            date=datetime(2025, 2, 18, 14, 0),
            tier=TierClassification.ORDINARY,
            turns=SAMPLE_TURNS[:2],
        )

        pipeline.process(transcript)

        # Retrieve from store
        stored = pipeline.stores["ordinary"].get_meeting("e2e_retrieve_001")
        assert stored is not None
        assert stored["metadata"]["meeting_id"] == "e2e_retrieve_001"
        assert stored["metadata"]["title"] == "Retrieve Test"  # title comes from transcript input

    def test_list_includes_stored_meeting(self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_embedding):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url)

        transcript = MeetingTranscript(
            meeting_id="e2e_list_001",
            title="List Test",
            date=datetime(2025, 2, 18, 14, 0),
            tier=TierClassification.ORDINARY,
            turns=SAMPLE_TURNS[:1],
        )

        pipeline.process(transcript)

        meetings = pipeline.stores["ordinary"].list_meetings()
        ids = [m["meeting_id"] for m in meetings]
        assert "e2e_list_001" in ids

    def test_search_finds_meeting(self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_embedding):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url)

        transcript = MeetingTranscript(
            meeting_id="e2e_search_001",
            title="Search Test",
            date=datetime(2025, 2, 18, 14, 0),
            tier=TierClassification.ORDINARY,
            turns=SAMPLE_TURNS[:2],
        )

        pipeline.process(transcript)

        results = pipeline.search_meetings("deployment", tier=TierClassification.ORDINARY)
        assert len(results) > 0
        assert any(r["meeting_id"] == "e2e_search_001" for r in results)

    def test_delete_removes_meeting(self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_embedding):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url)

        transcript = MeetingTranscript(
            meeting_id="e2e_delete_001",
            title="Delete Test",
            date=datetime(2025, 2, 18, 14, 0),
            tier=TierClassification.ORDINARY,
            turns=SAMPLE_TURNS[:1],
        )

        pipeline.process(transcript)
        assert pipeline.stores["ordinary"].get_meeting("e2e_delete_001") is not None

        pipeline.stores["ordinary"].delete_meeting("e2e_delete_001")
        assert pipeline.stores["ordinary"].get_meeting("e2e_delete_001") is None


class TestSensitivePipelineE2E:
    """Full flow with sensitive tier: redaction -> process -> store."""

    def test_sensitive_applies_redaction(
        self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_presidio, mock_embedding
    ):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url, enable_redaction=True)

        transcript = MeetingTranscript(
            meeting_id="e2e_sensitive_001",
            title="Security Audit",
            date=datetime(2025, 2, 18, 15, 0),
            tier=TierClassification.SENSITIVE,
            participants=SAMPLE_SPEAKERS,
            raw_text="john@stormgeo.com mentioned in the meeting about deployment.",
        )

        result = pipeline.process(transcript)

        assert result.tier == TierClassification.SENSITIVE
        assert result.meeting_id == "e2e_sensitive_001"
        assert result.vector_id is not None
        assert "sensitive" in result.vector_id

    def test_sensitive_stored_in_separate_namespace(
        self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_presidio, mock_embedding
    ):
        from backend.pipeline import MeetingPipeline

        pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url, enable_redaction=True)

        transcript = MeetingTranscript(
            meeting_id="e2e_sensitive_ns_001",
            title="Namespace Test",
            date=datetime(2025, 2, 18, 15, 0),
            tier=TierClassification.SENSITIVE,
            raw_text="Sensitive content with john@stormgeo.com PII data.",
        )

        pipeline.process(transcript)

        # Should be in sensitive store, not ordinary
        assert pipeline.stores["sensitive"].get_meeting("e2e_sensitive_ns_001") is not None
        assert pipeline.stores["ordinary"].get_meeting("e2e_sensitive_ns_001") is None


class TestAPIEndToEnd:
    """E2E through the FastAPI layer using TestClient."""

    def test_full_api_flow(
        self, fake_redis_url, mock_llm_extractor, mock_sentiment, mock_embedding
    ):
        import backend.api as api_module
        from backend.pipeline import MeetingPipeline
        from fastapi.testclient import TestClient

        test_pipeline = MeetingPipeline(api_key="test-key", redis_url=fake_redis_url)
        original = api_module.pipeline

        # Patch MeetingPipeline to prevent the lifespan from creating a second pipeline
        with patch("backend.api.MeetingPipeline"):
            with TestClient(api_module.app, raise_server_exceptions=False) as client:
                api_module.pipeline = test_pipeline

                # 1. Process a meeting
                resp = client.post("/api/v1/meetings/process", json={
                    "meeting_id": "e2e_api_001",
                    "title": "API E2E Test",
                    "tier": "ordinary",
                    "transcript": "Alice: Let's discuss the deployment. Bob: Sounds good, let's plan it.",
                })
                assert resp.status_code == 200
                data = resp.json()
                assert data["meeting_id"] == "e2e_api_001"
                assert data["status"] == "processed"

                # 2. List meetings — should include our meeting
                resp = client.get("/api/v1/meetings?tier=ordinary")
                assert resp.status_code == 200
                meetings = resp.json()["meetings"]
                ids = [m["meeting_id"] for m in meetings]
                assert "e2e_api_001" in ids

                # 3. Get specific meeting
                resp = client.get("/api/v1/meetings/e2e_api_001?tier=ordinary")
                assert resp.status_code == 200
                assert resp.json()["metadata"]["meeting_id"] == "e2e_api_001"

                # 4. Get transcript
                resp = client.get("/api/v1/meetings/e2e_api_001/transcript?tier=ordinary")
                assert resp.status_code == 200
                assert "Alice" in resp.json()["transcript"]

                # 5. Search
                resp = client.get("/api/v1/meetings/search?q=deployment")
                assert resp.status_code == 200
                results = resp.json()["results"]
                assert len(results) > 0

                # 6. Stats
                resp = client.get("/api/v1/stats")
                assert resp.status_code == 200
                assert resp.json()["total_meetings"] >= 1

                # 7. Delete
                resp = client.delete("/api/v1/meetings/e2e_api_001?tier=ordinary")
                assert resp.status_code == 200

                # 8. Verify deleted
                resp = client.get("/api/v1/meetings/e2e_api_001?tier=ordinary")
                assert resp.status_code == 404

        api_module.pipeline = original
