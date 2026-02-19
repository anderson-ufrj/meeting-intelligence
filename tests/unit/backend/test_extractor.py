"""Tests for the LLM extraction module (Phase 2)."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.models import MeetingInsights, MeetingTranscript, Speaker, TierClassification


class TestMeetingExtractorInit:
    def test_init_with_api_key(self, mock_anthropic):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="test-key-123")
        assert extractor.model == "claude-haiku-4-5-20251001"

    def test_init_from_env(self, mock_anthropic):
        from backend.extractor import MeetingExtractor
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key-456"}):
            extractor = MeetingExtractor()
            assert extractor.model == "claude-haiku-4-5-20251001"

    def test_init_no_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove ANTHROPIC_API_KEY if present
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ValueError, match="Anthropic API key required"):
                from backend.extractor import MeetingExtractor
                MeetingExtractor()

    def test_custom_model(self, mock_anthropic):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="key", model="claude-sonnet-4-20250514")
        assert extractor.model == "claude-sonnet-4-20250514"


class TestMeetingExtractorExtract:
    def test_extract_returns_insights(self, mock_anthropic, sample_transcript, sample_insights):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="test-key")
        result = extractor.extract(sample_transcript)

        assert isinstance(result, MeetingInsights)
        assert result.meeting_title == sample_transcript.title
        mock_anthropic.messages.create.assert_called_once()

    def test_extract_sets_title_and_date(self, mock_anthropic, sample_transcript, sample_insights):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="test-key")
        result = extractor.extract(sample_transcript)

        assert result.meeting_title == "Sprint Review Q1"
        assert result.meeting_date == sample_transcript.date.isoformat()


class TestBuildContext:
    def test_with_turns(self, mock_anthropic, sample_transcript):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="test-key")
        context = extractor._build_context(sample_transcript)

        assert "Sprint Review Q1" in context
        assert "[00:00:15] Alice Johnson:" in context
        assert "[00:01:30] Bob Smith:" in context

    def test_with_raw_text(self, mock_anthropic):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="test-key")

        transcript = MeetingTranscript(
            meeting_id="m1",
            title="Test Meeting",
            date=datetime(2025, 1, 1),
            raw_text="Alice: Hello everyone\nBob: Hi there",
        )
        context = extractor._build_context(transcript)

        assert "Alice: Hello everyone" in context
        assert "Bob: Hi there" in context

    def test_includes_participants(self, mock_anthropic, sample_transcript):
        from backend.extractor import MeetingExtractor
        extractor = MeetingExtractor(api_key="test-key")
        context = extractor._build_context(sample_transcript)

        assert "Alice Johnson" in context
        assert "Bob Smith" in context
        assert "Carol Davis" in context
