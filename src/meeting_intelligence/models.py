"""Pydantic models for structured meeting extraction."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TierClassification(str, Enum):
    """Privacy tier classification for meetings."""
    ORDINARY = "ordinary"
    SENSITIVE = "sensitive"


class Speaker(BaseModel):
    """A meeting participant."""
    name: str
    email: Optional[str] = None
    role: Optional[str] = None


class DialogueTurn(BaseModel):
    """A single speaker turn in the transcript."""
    timestamp: str
    speaker: str
    text: str


class Decision(BaseModel):
    """An extracted decision from the meeting."""
    topic: str = Field(description="What the decision is about")
    decision: str = Field(description="The actual decision made")
    deciders: List[str] = Field(description="Who made or approved the decision")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in extraction")


class ActionItem(BaseModel):
    """A task assigned during the meeting."""
    task: str = Field(description="What needs to be done")
    owner: str = Field(description="Who is responsible")
    deadline: Optional[str] = Field(None, description="When it should be completed")
    priority: Optional[str] = Field(None, description="Priority level")


class Topic(BaseModel):
    """A key topic discussed in the meeting."""
    name: str
    importance: str = Field(description="high/medium/low")
    related_speakers: List[str] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    """An unresolved question from the meeting."""
    question: str
    context: str
    stakeholders: List[str] = Field(default_factory=list)


class MeetingInsights(BaseModel):
    """Complete structured output from meeting analysis."""
    meeting_title: str
    meeting_date: Optional[str] = None
    summary: str = Field(description="Brief summary of the meeting")
    decisions: List[Decision] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    key_topics: List[Topic] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list)


class SentimentResult(BaseModel):
    """Sentiment analysis for a speaker."""
    speaker: str
    overall_sentiment: str = Field(description="positive/neutral/negative")
    confidence: float = Field(ge=0.0, le=1.0)
    key_phrases: List[str] = Field(default_factory=list)


class MeetingTranscript(BaseModel):
    """Input transcript model."""
    meeting_id: str
    title: str
    date: datetime
    tier: TierClassification = TierClassification.ORDINARY
    participants: List[Speaker] = Field(default_factory=list)
    turns: List[DialogueTurn] = Field(default_factory=list)
    raw_text: Optional[str] = None


class ProcessedMeeting(BaseModel):
    """Output after full pipeline processing."""
    meeting_id: str
    tier: TierClassification
    insights: MeetingInsights
    sentiments: List[SentimentResult] = Field(default_factory=list)
    vector_id: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    audit_log: List[dict] = Field(default_factory=list)
