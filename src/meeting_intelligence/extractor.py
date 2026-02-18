"""Structured extraction using Instructor + Pydantic."""

import os
from typing import Optional

import instructor
from openai import OpenAI

from .models import MeetingInsights, MeetingTranscript


class MeetingExtractor:
    """Extract structured insights from meeting transcripts using LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize the extractor with OpenAI credentials.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for extraction
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = instructor.from_openai(OpenAI(api_key=api_key))
        self.model = model
    
    def extract(self, transcript: MeetingTranscript) -> MeetingInsights:
        """Extract structured insights from a meeting transcript.
        
        Args:
            transcript: The meeting transcript to analyze
            
        Returns:
            MeetingInsights with decisions, action items, topics, etc.
        """
        # Build context from transcript
        context = self._build_context(transcript)
        
        # Extract using Instructor with Pydantic schema
        insights = self.client.chat.completions.create(
            model=self.model,
            response_model=MeetingInsights,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert meeting analyst. Extract structured insights "
                        "from the provided transcript. Be thorough but concise. "
                        "Only extract information explicitly stated in the transcript."
                    )
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            max_retries=3
        )
        
        # Fill in meeting metadata
        insights.meeting_title = transcript.title
        insights.meeting_date = transcript.date.isoformat() if transcript.date else None
        
        return insights
    
    def _build_context(self, transcript: MeetingTranscript) -> str:
        """Build the prompt context from transcript data."""
        lines = [
            f"Meeting: {transcript.title}",
            f"Date: {transcript.date}",
            f"Participants: {', '.join(p.name for p in transcript.participants)}",
            "\n--- Transcript ---\n"
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
    api_key: Optional[str] = None
) -> MeetingInsights:
    """Convenience function for quick extraction.
    
    Args:
        transcript_text: Raw transcript text
        title: Meeting title
        api_key: OpenAI API key
        
    Returns:
        Extracted meeting insights
    """
    from datetime import datetime
    
    transcript = MeetingTranscript(
        meeting_id="quick_extract",
        title=title,
        date=datetime.now(),
        raw_text=transcript_text
    )
    
    extractor = MeetingExtractor(api_key=api_key)
    return extractor.extract(transcript)
