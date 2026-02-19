"""E2E test fixtures — real pipeline wiring with fakeredis + mock LLM."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from backend.models import (
    ActionItem,
    Decision,
    MeetingInsights,
    SentimentResult,
    Topic,
)


@pytest.fixture(scope="module")
def fake_redis_server():
    """Shared fakeredis server for the entire E2E module."""
    return fakeredis.FakeServer()


@pytest.fixture
def fake_redis_url(fake_redis_server):
    """Patch redis.from_url to use fakeredis."""
    def _fake_from_url(url, **kwargs):
        return fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)

    with patch("backend.vectorstore.redis.from_url", side_effect=_fake_from_url):
        yield "redis://fake:6379"


@pytest.fixture
def mock_llm_extractor():
    """Mock the LLM extractor to return realistic insights without API calls."""
    insights = MeetingInsights(
        meeting_title="Sprint Planning Q1",
        meeting_date="2025-02-18",
        summary="Team discussed sprint goals, deployment timeline, and resource allocation.",
        decisions=[
            Decision(
                topic="Deployment",
                decision="Deploy to production on Friday after QA sign-off",
                deciders=["Alice Johnson", "Bob Smith"],
                confidence=0.92,
            ),
            Decision(
                topic="Resource Allocation",
                decision="Hire one more backend engineer",
                deciders=["Alice Johnson"],
                confidence=0.78,
            ),
        ],
        action_items=[
            ActionItem(task="Write deployment runbook", owner="Bob Smith", deadline="2025-02-20", priority="high"),
            ActionItem(task="Schedule QA review", owner="Carol Davis", priority="medium"),
        ],
        key_topics=[
            Topic(name="Deployment Pipeline", importance="high", related_speakers=["Bob Smith"]),
            Topic(name="Hiring", importance="medium", related_speakers=["Alice Johnson"]),
        ],
    )

    with patch("backend.extractor.instructor.from_anthropic") as mock_instructor, \
         patch("backend.extractor.anthropic.Anthropic"):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = insights
        mock_instructor.return_value = mock_client
        yield insights


@pytest.fixture
def mock_sentiment():
    """Mock the BERT sentiment analyzer."""
    with patch("backend.sentiment.pipeline") as mock_pipeline:
        def fake_classifier(text, **kwargs):
            return [{"label": "4 stars", "score": 0.82}]

        mock_pipeline.return_value = fake_classifier
        yield mock_pipeline


@pytest.fixture
def mock_presidio():
    """Mock Presidio for redaction tests."""
    with patch("backend.redaction.AnalyzerEngine") as mock_analyzer_cls, \
         patch("backend.redaction.AnonymizerEngine") as mock_anonymizer_cls:

        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()
        mock_analyzer_cls.return_value = mock_analyzer
        mock_anonymizer_cls.return_value = mock_anonymizer

        # Simulate detecting an email
        email_result = MagicMock()
        email_result.entity_type = "EMAIL_ADDRESS"
        email_result.start = 0
        email_result.end = 16
        email_result.score = 0.95
        mock_analyzer.analyze.return_value = [email_result]

        anonymized = MagicMock()
        anonymized.text = "<EMAIL_ADDRESS> mentioned in the meeting about deployment."
        mock_anonymizer.anonymize.return_value = anonymized

        yield mock_analyzer, mock_anonymizer


@pytest.fixture
def mock_embedding():
    """Mock SentenceTransformer to avoid loading the model."""
    import numpy as np

    with patch("backend.vectorstore.SentenceTransformer", create=True) as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model
        yield mock_model
