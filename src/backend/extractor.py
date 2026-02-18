"""Structured extraction using Instructor + Anthropic Claude."""

import os
from typing import Optional

import anthropic
import instructor

from .models import MeetingInsights, MeetingTranscript


class MeetingExtractor:
    """Extract structured insights from meeting transcripts using Claude."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key required (ANTHROPIC_API_KEY)")

        self.client = instructor.from_anthropic(
            anthropic.Anthropic(api_key=api_key)
        )
        self.model = model

    def extract(self, transcript: MeetingTranscript) -> MeetingInsights:
        """Extract structured insights from a meeting transcript."""
        context = self._build_context(transcript)

        insights = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            response_model=MeetingInsights,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an expert meeting analyst. Extract structured insights "
                        "from the provided transcript. Be thorough but concise. "
                        "Only extract information explicitly stated in the transcript.\n\n"
                        f"{context}"
                    ),
                }
            ],
            max_retries=3,
        )

        insights.meeting_title = transcript.title
        insights.meeting_date = transcript.date.isoformat() if transcript.date else None

        return insights

    def _build_context(self, transcript: MeetingTranscript) -> str:
        """Build the prompt context from transcript data."""
        lines = [
            f"Meeting: {transcript.title}",
            f"Date: {transcript.date}",
            f"Participants: {', '.join(p.name for p in transcript.participants)}",
            "\n--- Transcript ---\n",
        ]

        if transcript.turns:
            for turn in transcript.turns:
                lines.append(f"[{turn.timestamp}] {turn.speaker}: {turn.text}")
        elif transcript.raw_text:
            lines.append(transcript.raw_text)

        return "\n".join(lines)


def extract_meeting_insights(
    transcript_text: str,
    title: str = "Unknown Meeting",
    api_key: Optional[str] = None,
) -> MeetingInsights:
    """Convenience function for quick extraction."""
    from datetime import datetime

    transcript = MeetingTranscript(
        meeting_id="quick_extract",
        title=title,
        date=datetime.now(),
        raw_text=transcript_text,
    )

    extractor = MeetingExtractor(api_key=api_key)
    return extractor.extract(transcript)
