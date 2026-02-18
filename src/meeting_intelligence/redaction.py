"""PII redaction for sensitive tier meetings."""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


@dataclass
class RedactionResult:
    """Result of PII redaction."""
    redacted_text: str
    entities_found: List[Dict]
    redaction_count: int


class PIIRedactor:
    """Redact personally identifiable information from transcripts."""
    
    # Default entities to redact
    DEFAULT_ENTITIES = [
        "PERSON",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "CREDIT_CARD",
        "IBAN_CODE",
        "LOCATION",
        "DATE_TIME",
        "NRP",  # Nationality, religious or political group
    ]
    
    def __init__(self, language: str = "en"):
        """Initialize the PII redactor.
        
        Args:
            language: Language for analysis (en, es, etc.)
        """
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.language = language
    
    def redact(
        self,
        text: str,
        entities: Optional[List[str]] = None,
        replacement_format: str = "<{entity_type}>"
    ) -> RedactionResult:
        """Redact PII from text.
        
        Args:
            text: Text to redact
            entities: List of entity types to redact (default: all)
            replacement_format: Format for replacement text
            
        Returns:
            RedactionResult with redacted text and metadata
        """
        entities = entities or self.DEFAULT_ENTITIES
        
        # Analyze for PII
        analyzer_results = self.analyzer.analyze(
            text=text,
            language=self.language,
            entities=entities
        )
        
        # Build operators for each entity type
        operators = {}
        for entity_type in set(r.entity_type for r in analyzer_results):
            operators[entity_type] = OperatorConfig(
                "replace",
                {"new_value": replacement_format.format(entity_type=entity_type)}
            )
        
        # Anonymize
        if analyzer_results:
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operators
            )
            redacted_text = anonymized_result.text
        else:
            redacted_text = text
        
        # Build entity list
        entities_found = [
            {
                "type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score
            }
            for r in analyzer_results
        ]
        
        return RedactionResult(
            redacted_text=redacted_text,
            entities_found=entities_found,
            redaction_count=len(analyzer_results)
        )
    
    def redact_transcript(
        self,
        transcript_text: str,
        preserve_speakers: Optional[List[str]] = None
    ) -> RedactionResult:
        """Redact PII from a meeting transcript, optionally preserving speaker names.
        
        Args:
            transcript_text: Full transcript text
            preserve_speakers: List of speaker names to keep (redact other names)
            
        Returns:
            RedactionResult with redacted transcript
        """
        # First pass: redact all PII
        result = self.redact(transcript_text)
        
        # If we need to preserve certain speakers, restore them
        if preserve_speakers:
            redacted_text = result.redacted_text
            for speaker in preserve_speakers:
                # Replace <PERSON> with actual speaker name when it's them
                # This is a simplified approach
                pattern = rf"\[([\d:]+)\] <PERSON>:"
                redacted_text = re.sub(
                    pattern,
                    lambda m: f"[{m.group(1)}] {speaker}:"
                    if speaker in transcript_text else m.group(0),
                    redacted_text
                )
            result.redacted_text = redacted_text
        
        return result
    
    def get_audit_log_entry(
        self,
        meeting_id: str,
        result: RedactionResult,
        user: Optional[str] = None
    ) -> Dict:
        """Generate an audit log entry for redaction.
        
        Args:
            meeting_id: ID of the meeting
            result: Redaction result
            user: User who triggered the redaction
            
        Returns:
            Audit log entry dict
        """
        from datetime import datetime
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "meeting_id": meeting_id,
            "action": "pii_redaction",
            "user": user or "system",
            "entities_redacted": result.redaction_count,
            "entity_types": list(set(e["type"] for e in result.entities_found))
        }


# Simple regex-based fallback for quick redaction without Presidio
def simple_redact(text: str) -> str:
    """Quick regex-based redaction for common PII patterns.
    
    Args:
        text: Text to redact
        
    Returns:
        Redacted text
    """
    patterns = {
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    }
    
    result = text
    for entity_type, pattern in patterns.items():
        result = re.sub(pattern, f"<{entity_type}>", result)
    
    return result
