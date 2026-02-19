"""Shared fixtures for the Meeting Intelligence test suite."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.models import (
    ActionItem,
    Decision,
    DialogueTurn,
    MeetingInsights,
    MeetingTranscript,
    OpenQuestion,
    ProcessedMeeting,
    SentimentResult,
    Speaker,
    TierClassification,
    Topic,
)


# ── Sample data ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_speakers():
    return [
        Speaker(name="Alice Johnson", email="alice@stormgeo.com", role="PM"),
        Speaker(name="Bob Smith", email="bob@stormgeo.com", role="Engineer"),
        Speaker(name="Carol Davis", role="Designer"),
    ]


@pytest.fixture
def sample_turns():
    return [
        DialogueTurn(timestamp="00:00:15", speaker="Alice Johnson", text="Let's start with the sprint review."),
        DialogueTurn(timestamp="00:01:30", speaker="Bob Smith", text="I finished the API refactoring. Tests are green."),
        DialogueTurn(timestamp="00:02:45", speaker="Carol Davis", text="The new mockups are ready for review."),
        DialogueTurn(timestamp="00:04:00", speaker="Alice Johnson", text="Great. Let's decide on the deployment date."),
        DialogueTurn(timestamp="00:05:10", speaker="Bob Smith", text="I suggest we deploy next Friday after QA."),
        DialogueTurn(timestamp="00:06:20", speaker="Alice Johnson", text="Agreed. Bob, can you prepare the release notes?"),
    ]


@pytest.fixture
def sample_transcript(sample_speakers, sample_turns):
    return MeetingTranscript(
        meeting_id="test_meeting_001",
        title="Sprint Review Q1",
        date=datetime(2025, 2, 18, 14, 0),
        tier=TierClassification.ORDINARY,
        participants=sample_speakers,
        turns=sample_turns,
    )


@pytest.fixture
def sample_sensitive_transcript(sample_speakers, sample_turns):
    return MeetingTranscript(
        meeting_id="test_meeting_002",
        title="Security Audit Review",
        date=datetime(2025, 2, 18, 15, 0),
        tier=TierClassification.SENSITIVE,
        participants=sample_speakers,
        turns=sample_turns,
        raw_text="[00:00:15] Alice Johnson: Contact john@example.com for the report.",
    )


@pytest.fixture
def sample_insights():
    return MeetingInsights(
        meeting_title="Sprint Review Q1",
        meeting_date="2025-02-18",
        summary="Sprint review covering API refactoring, mockup delivery, and deployment planning.",
        decisions=[
            Decision(
                topic="Deployment",
                decision="Deploy next Friday after QA",
                deciders=["Alice Johnson", "Bob Smith"],
                confidence=0.92,
            ),
        ],
        action_items=[
            ActionItem(
                task="Prepare release notes",
                owner="Bob Smith",
                deadline="2025-02-21",
                priority="high",
            ),
            ActionItem(
                task="Review mockups",
                owner="Alice Johnson",
            ),
        ],
        key_topics=[
            Topic(name="API Refactoring", importance="high", related_speakers=["Bob Smith"]),
            Topic(name="Deployment Planning", importance="high", related_speakers=["Alice Johnson", "Bob Smith"]),
            Topic(name="UI Mockups", importance="medium", related_speakers=["Carol Davis"]),
        ],
        open_questions=[
            OpenQuestion(
                question="Who handles the post-deployment monitoring?",
                context="No one was assigned for on-call after the Friday deploy.",
                stakeholders=["Bob Smith"],
            ),
        ],
    )


@pytest.fixture
def sample_sentiments():
    return [
        SentimentResult(speaker="Alice Johnson", overall_sentiment="positive", confidence=0.85, key_phrases=["Let's start with the sprint"]),
        SentimentResult(speaker="Bob Smith", overall_sentiment="positive", confidence=0.78, key_phrases=["I finished the API refactoring"]),
        SentimentResult(speaker="Carol Davis", overall_sentiment="neutral", confidence=0.65, key_phrases=["The new mockups are ready"]),
    ]


@pytest.fixture
def sample_processed_meeting(sample_insights, sample_sentiments):
    return ProcessedMeeting(
        meeting_id="test_meeting_001",
        tier=TierClassification.ORDINARY,
        insights=sample_insights,
        sentiments=sample_sentiments,
        vector_id="ordinary_test_meeting_001",
        audit_log=[
            {"step": "classification", "tier": "ordinary"},
            {"step": "extraction", "model": "claude-haiku-4-5-20251001"},
            {"step": "sentiment", "speakers_analyzed": 3},
            {"step": "storage", "vector_id": "ordinary_test_meeting_001"},
        ],
    )


# ── Mock helpers ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_redis():
    """Patch redis.from_url to return a MagicMock."""
    with patch("redis.from_url") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_anthropic(sample_insights):
    """Patch instructor.from_anthropic to return a mock that yields sample_insights."""
    with patch("backend.extractor.instructor.from_anthropic") as mock_instructor, \
         patch("backend.extractor.anthropic.Anthropic"):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = sample_insights
        mock_instructor.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_sentiment_classifier():
    """Patch transformers.pipeline to return a fake classifier."""
    with patch("backend.sentiment.pipeline") as mock_pipeline:
        def fake_classifier(text, **kwargs):
            return [{"label": "4 stars", "score": 0.82}]

        mock_pipeline.return_value = fake_classifier
        yield mock_pipeline
