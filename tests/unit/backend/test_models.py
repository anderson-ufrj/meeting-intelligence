"""Tests for Pydantic models (Phase 1)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

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


class TestTierClassification:
    def test_values(self):
        assert TierClassification.ORDINARY == "ordinary"
        assert TierClassification.SENSITIVE == "sensitive"

    def test_from_string(self):
        assert TierClassification("ordinary") == TierClassification.ORDINARY
        assert TierClassification("sensitive") == TierClassification.SENSITIVE

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            TierClassification("unknown")


class TestDecision:
    def test_valid(self):
        d = Decision(topic="Deploy", decision="Ship Friday", deciders=["Alice"], confidence=0.9)
        assert d.confidence == 0.9

    def test_confidence_lower_bound(self):
        d = Decision(topic="x", decision="y", deciders=[], confidence=0.0)
        assert d.confidence == 0.0

    def test_confidence_upper_bound(self):
        d = Decision(topic="x", decision="y", deciders=[], confidence=1.0)
        assert d.confidence == 1.0

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            Decision(topic="x", decision="y", deciders=[], confidence=-0.1)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            Decision(topic="x", decision="y", deciders=[], confidence=1.1)

    def test_serialization_roundtrip(self):
        d = Decision(topic="Deploy", decision="Friday", deciders=["A", "B"], confidence=0.8)
        data = d.model_dump()
        restored = Decision(**data)
        assert restored == d


class TestActionItem:
    def test_required_fields(self):
        a = ActionItem(task="Write docs", owner="Bob")
        assert a.task == "Write docs"
        assert a.owner == "Bob"

    def test_optional_fields_default_none(self):
        a = ActionItem(task="x", owner="y")
        assert a.deadline is None
        assert a.priority is None

    def test_with_all_fields(self):
        a = ActionItem(task="x", owner="y", deadline="2025-03-01", priority="high")
        assert a.deadline == "2025-03-01"
        assert a.priority == "high"


class TestSpeaker:
    def test_name_only(self):
        s = Speaker(name="Alice")
        assert s.email is None
        assert s.role is None

    def test_full(self):
        s = Speaker(name="Alice", email="alice@test.com", role="PM")
        assert s.email == "alice@test.com"


class TestTopic:
    def test_accepts_importance_values(self):
        for imp in ["high", "medium", "low"]:
            t = Topic(name="Test", importance=imp)
            assert t.importance == imp

    def test_related_speakers_default_empty(self):
        t = Topic(name="Test", importance="high")
        assert t.related_speakers == []


class TestOpenQuestion:
    def test_required_fields(self):
        q = OpenQuestion(question="Who monitors?", context="No one assigned")
        assert q.question == "Who monitors?"
        assert q.context == "No one assigned"

    def test_stakeholders_default_empty(self):
        q = OpenQuestion(question="?", context="ctx")
        assert q.stakeholders == []


class TestMeetingInsights:
    def test_defaults_empty_lists(self):
        mi = MeetingInsights(meeting_title="Test", summary="A summary")
        assert mi.decisions == []
        assert mi.action_items == []
        assert mi.key_topics == []
        assert mi.open_questions == []
        assert mi.meeting_date is None

    def test_with_data(self, sample_insights):
        assert len(sample_insights.decisions) == 1
        assert len(sample_insights.action_items) == 2
        assert len(sample_insights.key_topics) == 3
        assert len(sample_insights.open_questions) == 1


class TestSentimentResult:
    def test_valid(self):
        s = SentimentResult(speaker="Alice", overall_sentiment="positive", confidence=0.85)
        assert s.speaker == "Alice"
        assert s.key_phrases == []

    def test_serialization(self):
        s = SentimentResult(speaker="Bob", overall_sentiment="neutral", confidence=0.5, key_phrases=["good work"])
        data = s.model_dump()
        assert data["speaker"] == "Bob"
        assert data["key_phrases"] == ["good work"]

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            SentimentResult(speaker="X", overall_sentiment="pos", confidence=1.5)


class TestMeetingTranscript:
    def test_defaults(self):
        mt = MeetingTranscript(meeting_id="m1", title="Test", date=datetime.now())
        assert mt.tier == TierClassification.ORDINARY
        assert mt.participants == []
        assert mt.turns == []
        assert mt.raw_text is None

    def test_with_raw_text_only(self):
        mt = MeetingTranscript(
            meeting_id="m1", title="Test", date=datetime.now(),
            raw_text="Alice: Hello\nBob: Hi",
        )
        assert mt.raw_text is not None
        assert mt.turns == []

    def test_with_turns_only(self, sample_turns):
        mt = MeetingTranscript(
            meeting_id="m1", title="Test", date=datetime.now(),
            turns=sample_turns,
        )
        assert len(mt.turns) == 6
        assert mt.raw_text is None


class TestProcessedMeeting:
    def test_auto_timestamp(self, sample_insights):
        before = datetime.utcnow()
        pm = ProcessedMeeting(
            meeting_id="m1",
            tier=TierClassification.ORDINARY,
            insights=sample_insights,
        )
        after = datetime.utcnow()
        assert before <= pm.processed_at <= after

    def test_defaults(self, sample_insights):
        pm = ProcessedMeeting(
            meeting_id="m1",
            tier=TierClassification.ORDINARY,
            insights=sample_insights,
        )
        assert pm.sentiments == []
        assert pm.vector_id is None
        assert pm.audit_log == []

    def test_full(self, sample_processed_meeting):
        pm = sample_processed_meeting
        assert pm.meeting_id == "test_meeting_001"
        assert pm.tier == TierClassification.ORDINARY
        assert len(pm.sentiments) == 3
        assert pm.vector_id == "ordinary_test_meeting_001"
        assert len(pm.audit_log) == 4
