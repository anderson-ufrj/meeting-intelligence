"""Pipeline orchestrator for meeting processing."""

import os
from typing import Optional, List, Dict
from datetime import datetime

from .models import (
    MeetingTranscript,
    MeetingInsights,
    SentimentResult,
    ProcessedMeeting,
    TierClassification
)
from .extractor import MeetingExtractor
from .sentiment import SentimentAnalyzer
from .vectorstore import MeetingVectorStore, create_tiered_stores
from .redaction import PIIRedactor


class MeetingPipeline:
    """End-to-end pipeline for processing meeting transcripts."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        redis_url: Optional[str] = None,
        enable_redaction: bool = True,
    ):
        """Initialize the pipeline.

        Args:
            api_key: OpenAI API key
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
            enable_redaction: Whether to enable PII redaction for sensitive tier
        """
        self.extractor = MeetingExtractor(api_key=api_key)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.enable_redaction = enable_redaction

        if enable_redaction:
            self.redactor = PIIRedactor()

        # Create tiered vector stores (Redis-backed)
        self.stores = create_tiered_stores(redis_url)
    
    def process(
        self,
        transcript: MeetingTranscript,
        user: Optional[str] = None
    ) -> ProcessedMeeting:
        """Process a meeting transcript through the full pipeline.
        
        Args:
            transcript: Meeting transcript to process
            user: User triggering the processing (for audit)
            
        Returns:
            Processed meeting with insights, sentiment, and storage info
        """
        audit_log: List[Dict] = []
        
        # Step 1: Tier classification (if not already set)
        tier = transcript.tier
        audit_log.append({
            "step": "classification",
            "tier": tier.value,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Step 2: Redaction for sensitive tier
        redacted_text = None
        if tier == TierClassification.SENSITIVE and self.enable_redaction:
            raw_text = transcript.raw_text or self._turns_to_text(transcript.turns)
            redaction_result = self.redactor.redact_transcript(raw_text)
            redacted_text = redaction_result.redacted_text
            
            audit_log.append({
                "step": "redaction",
                "entities_redacted": redaction_result.redaction_count,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Create redacted transcript for extraction
            transcript = self._create_redacted_transcript(transcript, redacted_text)
        
        # Step 3: Extract insights
        insights = self.extractor.extract(transcript)
        audit_log.append({
            "step": "extraction",
            "model": self.extractor.model,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Step 4: Sentiment analysis
        sentiments = self.sentiment_analyzer.analyze_meeting(transcript)
        audit_log.append({
            "step": "sentiment",
            "speakers_analyzed": len(sentiments),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Step 5: Create processed meeting
        processed = ProcessedMeeting(
            meeting_id=transcript.meeting_id,
            tier=tier,
            insights=insights,
            sentiments=sentiments,
            audit_log=audit_log
        )
        
        # Step 6: Store in vector DB
        namespace = tier.value
        vector_id = self.stores[tier.value].add_meeting(processed, namespace=namespace)
        processed.vector_id = vector_id
        
        audit_log.append({
            "step": "storage",
            "vector_id": vector_id,
            "namespace": namespace,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return processed
    
    def search_meetings(
        self,
        query: str,
        tier: Optional[TierClassification] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search across processed meetings.
        
        Args:
            query: Search query
            tier: Optional tier filter
            n_results: Number of results
            
        Returns:
            List of search results
        """
        if tier:
            results = self.stores[tier.value].search(
                query,
                namespace=tier.value,
                n_results=n_results
            )
        else:
            # Search ordinary tier only by default
            results = self.stores["ordinary"].search(
                query,
                namespace="ordinary",
                n_results=n_results
            )
        
        return [
            {
                "meeting_id": r.meeting_id,
                "score": r.score,
                "title": r.metadata.get("title", "Unknown"),
                "tier": r.metadata.get("tier", "unknown"),
                "content_preview": r.content[:200] + "..."
            }
            for r in results
        ]
    
    def _turns_to_text(self, turns: List) -> str:
        """Convert dialogue turns to text."""
        if not turns:
            return ""
        return "\n".join(f"[{t.timestamp}] {t.speaker}: {t.text}" for t in turns)
    
    def _create_redacted_transcript(
        self,
        original: MeetingTranscript,
        redacted_text: str
    ) -> MeetingTranscript:
        """Create a new transcript with redacted text."""
        return MeetingTranscript(
            meeting_id=original.meeting_id,
            title=original.title,
            date=original.date,
            tier=original.tier,
            participants=original.participants,
            raw_text=redacted_text
        )


def quick_process(
    transcript_text: str,
    title: str = "Unknown Meeting",
    tier: TierClassification = TierClassification.ORDINARY,
    api_key: Optional[str] = None
) -> ProcessedMeeting:
    """Quick one-off processing of a transcript.
    
    Args:
        transcript_text: Raw transcript text
        title: Meeting title
        tier: Privacy tier
        api_key: OpenAI API key
        
    Returns:
        Fully processed meeting
    """
    from .models import DialogueTurn
    
    transcript = MeetingTranscript(
        meeting_id=f"quick_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        title=title,
        date=datetime.now(),
        tier=tier,
        raw_text=transcript_text
    )
    
    pipeline = MeetingPipeline(api_key=api_key, redis_url=os.getenv("REDIS_URL"))
    return pipeline.process(transcript)
