"""BERT-based sentiment analysis per speaker."""

from typing import List, Dict
from collections import defaultdict

from transformers import pipeline

from .models import SentimentResult, MeetingTranscript, DialogueTurn


class SentimentAnalyzer:
    """Analyze sentiment per speaker using BERT."""
    
    def __init__(self, model: str = "nlptown/bert-base-multilingual-uncased-sentiment"):
        """Initialize the sentiment analyzer.
        
        Args:
            model: HuggingFace model for sentiment analysis
        """
        # Load sentiment pipeline
        # This model outputs 1-5 stars (1 = very negative, 5 = very positive)
        self.classifier = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=model
        )
    
    def analyze_meeting(self, transcript: MeetingTranscript) -> List[SentimentResult]:
        """Analyze sentiment for each speaker in the meeting.
        
        Args:
            transcript: Meeting transcript with dialogue turns
            
        Returns:
            List of sentiment results per speaker
        """
        # Group turns by speaker
        speaker_turns: Dict[str, List[str]] = defaultdict(list)
        
        if transcript.turns:
            for turn in transcript.turns:
                speaker_turns[turn.speaker].append(turn.text)
        elif transcript.raw_text:
            # Parse raw text if needed
            speaker_turns = self._parse_raw_transcript(transcript.raw_text)
        
        # Analyze each speaker
        results = []
        for speaker, texts in speaker_turns.items():
            sentiment = self._analyze_speaker(speaker, texts)
            results.append(sentiment)
        
        return results
    
    def _analyze_speaker(self, speaker: str, texts: List[str]) -> SentimentResult:
        """Analyze sentiment for a single speaker's contributions."""
        if not texts:
            return SentimentResult(
                speaker=speaker,
                overall_sentiment="neutral",
                confidence=0.0,
                key_phrases=[]
            )
        
        # Combine all texts from this speaker
        combined_text = " ".join(texts[:10])  # Limit to avoid token limits
        
        # Get sentiment
        result = self.classifier(combined_text[:512])[0]  # Truncate if needed
        
        # Map 1-5 stars to sentiment labels
        label = result["label"]
        score = result["score"]
        
        # Extract star rating from label (e.g., "1 star" -> 1)
        star_rating = int(label.split()[0])
        
        # Map to sentiment
        if star_rating <= 2:
            sentiment = "negative"
        elif star_rating == 3:
            sentiment = "neutral"
        else:
            sentiment = "positive"
        
        # Extract key phrases (simplified - could use NER or keyword extraction)
        key_phrases = self._extract_key_phrases(texts)
        
        return SentimentResult(
            speaker=speaker,
            overall_sentiment=sentiment,
            confidence=score,
            key_phrases=key_phrases
        )
    
    def _parse_raw_transcript(self, raw_text: str) -> Dict[str, List[str]]:
        """Parse raw transcript text to extract speaker turns."""
        speaker_turns: Dict[str, List[str]] = defaultdict(list)
        
        lines = raw_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("---"):
                continue
            
            # Try to parse [timestamp] Speaker: Text format
            if "]" in line and ":" in line:
                try:
                    parts = line.split("]", 1)
                    if len(parts) == 2:
                        rest = parts[1].strip()
                        if ":" in rest:
                            speaker, text = rest.split(":", 1)
                            speaker_turns[speaker.strip()].append(text.strip())
                except Exception:
                    pass
        
        return speaker_turns
    
    def _extract_key_phrases(self, texts: List[str]) -> List[str]:
        """Extract key phrases from speaker's contributions."""
        # Simplified implementation - could use RAKE, YAKE, or NER
        # For now, return first 3 non-trivial phrases
        phrases = []
        for text in texts:
            words = text.split()
            if len(words) > 3:
                phrase = " ".join(words[:8])
                if phrase not in phrases:
                    phrases.append(phrase)
            if len(phrases) >= 3:
                break
        return phrases


def analyze_sentiment_simple(text: str) -> Dict[str, any]:
    """Quick sentiment analysis for a text snippet.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dict with sentiment label and score
    """
    analyzer = SentimentAnalyzer()
    result = analyzer.classifier(text[:512])[0]
    return {
        "label": result["label"],
        "score": result["score"]
    }
