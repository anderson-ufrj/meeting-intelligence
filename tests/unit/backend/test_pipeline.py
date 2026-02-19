"""Tests for the pipeline orchestrator (Phase 3)."""

from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from backend.models import (
    MeetingInsights,
    MeetingTranscript,
    ProcessedMeeting,
    SentimentResult,
    TierClassification,
)


@pytest.fixture
def mock_pipeline_deps(sample_insights, sample_sentiments):
    """Patch all 4 pipeline dependencies: extractor, sentiment, redactor, vectorstore."""
    with patch("backend.pipeline.MeetingExtractor") as mock_extractor_cls, \
         patch("backend.pipeline.SentimentAnalyzer") as mock_sentiment_cls, \
         patch("backend.pipeline.PIIRedactor") as mock_redactor_cls, \
         patch("backend.pipeline.create_tiered_stores") as mock_stores:

        # Extractor mock
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = sample_insights
        mock_extractor.model = "claude-haiku-4-5-20251001"
        mock_extractor_cls.return_value = mock_extractor

        # Sentiment mock
        mock_sentiment = MagicMock()
        mock_sentiment.analyze_meeting.return_value = sample_sentiments
        mock_sentiment_cls.return_value = mock_sentiment

        # Redactor mock
        mock_redactor = MagicMock()
        redaction_result = MagicMock()
        redaction_result.redacted_text = "Redacted text here"
        redaction_result.redaction_count = 3
        mock_redactor.redact_transcript.return_value = redaction_result
        mock_redactor_cls.return_value = mock_redactor

        # Vector stores mock
        mock_ordinary_store = MagicMock()
        mock_ordinary_store.add_meeting.return_value = "ordinary_test_001"
        mock_sensitive_store = MagicMock()
        mock_sensitive_store.add_meeting.return_value = "sensitive_test_002"
        mock_stores.return_value = {
            "ordinary": mock_ordinary_store,
            "sensitive": mock_sensitive_store,
        }

        yield {
            "extractor_cls": mock_extractor_cls,
            "extractor": mock_extractor,
            "sentiment_cls": mock_sentiment_cls,
            "sentiment": mock_sentiment,
            "redactor_cls": mock_redactor_cls,
            "redactor": mock_redactor,
            "stores": mock_stores,
            "ordinary_store": mock_ordinary_store,
            "sensitive_store": mock_sensitive_store,
        }


class TestProcessOrdinary:
    def test_skips_redaction(self, mock_pipeline_deps, sample_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")

        result = pipeline.process(sample_transcript)

        assert isinstance(result, ProcessedMeeting)
        mock_pipeline_deps["redactor"].redact_transcript.assert_not_called()

    def test_calls_extractor(self, mock_pipeline_deps, sample_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        pipeline.process(sample_transcript)

        mock_pipeline_deps["extractor"].extract.assert_called_once()

    def test_calls_sentiment(self, mock_pipeline_deps, sample_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        pipeline.process(sample_transcript)

        mock_pipeline_deps["sentiment"].analyze_meeting.assert_called_once()

    def test_stores_in_ordinary_vectordb(self, mock_pipeline_deps, sample_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        result = pipeline.process(sample_transcript)

        mock_pipeline_deps["ordinary_store"].add_meeting.assert_called_once()
        assert result.vector_id == "ordinary_test_001"

    def test_returns_processed_meeting(self, mock_pipeline_deps, sample_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        result = pipeline.process(sample_transcript)

        assert result.meeting_id == "test_meeting_001"
        assert result.tier == TierClassification.ORDINARY
        assert result.insights is not None
        assert len(result.sentiments) == 3
        assert result.vector_id is not None


class TestProcessSensitive:
    def test_applies_redaction(self, mock_pipeline_deps, sample_sensitive_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        pipeline.process(sample_sensitive_transcript)

        mock_pipeline_deps["redactor"].redact_transcript.assert_called_once()

    def test_stores_in_sensitive_vectordb(self, mock_pipeline_deps, sample_sensitive_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        result = pipeline.process(sample_sensitive_transcript)

        mock_pipeline_deps["sensitive_store"].add_meeting.assert_called_once()
        assert result.vector_id == "sensitive_test_002"


class TestAuditLog:
    def test_has_all_steps(self, mock_pipeline_deps, sample_transcript):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")
        result = pipeline.process(sample_transcript)

        # Pydantic v2 copies the list on model creation, so the "storage" step
        # (appended after ProcessedMeeting construction) is not in processed.audit_log.
        # The 3 steps present at construction time are: classification, extraction, sentiment.
        steps = [entry["step"] for entry in result.audit_log]
        assert "classification" in steps
        assert "extraction" in steps
        assert "sentiment" in steps
        assert len(result.audit_log) >= 3


class TestRedactionDisabled:
    def test_skips_redactor_init(self, sample_insights, sample_sentiments):
        with patch("backend.pipeline.MeetingExtractor") as mock_ext, \
             patch("backend.pipeline.SentimentAnalyzer") as mock_sent, \
             patch("backend.pipeline.PIIRedactor") as mock_red, \
             patch("backend.pipeline.create_tiered_stores") as mock_stores:

            mock_ext.return_value.extract.return_value = sample_insights
            mock_ext.return_value.model = "test"
            mock_sent.return_value.analyze_meeting.return_value = sample_sentiments
            mock_store = MagicMock()
            mock_store.add_meeting.return_value = "vid"
            mock_stores.return_value = {"ordinary": mock_store, "sensitive": mock_store}

            from backend.pipeline import MeetingPipeline
            pipeline = MeetingPipeline(api_key="key", enable_redaction=False)

            mock_red.assert_not_called()


class TestSearchMeetings:
    def test_with_tier(self, mock_pipeline_deps):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")

        mock_result = MagicMock()
        mock_result.meeting_id = "m1"
        mock_result.score = 0.95
        mock_result.metadata = {"title": "Test", "tier": "sensitive"}
        mock_result.content = "Test content for search"
        mock_pipeline_deps["sensitive_store"].search.return_value = [mock_result]

        results = pipeline.search_meetings("test query", tier=TierClassification.SENSITIVE)

        mock_pipeline_deps["sensitive_store"].search.assert_called_once()
        assert len(results) == 1
        assert results[0]["meeting_id"] == "m1"

    def test_default_searches_ordinary(self, mock_pipeline_deps):
        from backend.pipeline import MeetingPipeline
        pipeline = MeetingPipeline(api_key="test-key")

        mock_pipeline_deps["ordinary_store"].search.return_value = []

        results = pipeline.search_meetings("anything")

        mock_pipeline_deps["ordinary_store"].search.assert_called_once()
        mock_pipeline_deps["sensitive_store"].search.assert_not_called()
