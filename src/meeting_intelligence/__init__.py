"""Meeting Intelligence: Two-tier pipeline for extracting insights from meeting transcripts."""

__version__ = "0.1.0"

from .pipeline import MeetingPipeline
from .models import (
    TierClassification,
    MeetingTranscript,
    MeetingInsights,
    ProcessedMeeting,
    SentimentResult,
)

__all__ = [
    "MeetingPipeline",
    "TierClassification",
    "MeetingTranscript",
    "MeetingInsights",
    "ProcessedMeeting",
    "SentimentResult",
]
