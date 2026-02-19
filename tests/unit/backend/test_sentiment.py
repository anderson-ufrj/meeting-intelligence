"""Tests for BERT sentiment analysis module (Phase 2)."""

from collections import defaultdict
from datetime import datetime

import pytest

from backend.models import DialogueTurn, MeetingTranscript, SentimentResult, TierClassification


class TestSentimentAnalyzerInit:
    def test_init_creates_classifier(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        mock_sentiment_classifier.assert_called_once_with(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            tokenizer="nlptown/bert-base-multilingual-uncased-sentiment",
        )


class TestAnalyzeMeeting:
    def test_with_turns(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        transcript = MeetingTranscript(
            meeting_id="m1",
            title="Test",
            date=datetime(2025, 1, 1),
            turns=[
                DialogueTurn(timestamp="00:00", speaker="Alice", text="Great progress today!"),
                DialogueTurn(timestamp="00:01", speaker="Bob", text="I agree, things look good."),
                DialogueTurn(timestamp="00:02", speaker="Alice", text="Let's keep it up."),
            ],
        )

        results = analyzer.analyze_meeting(transcript)

        assert len(results) == 2  # Alice and Bob
        speakers = {r.speaker for r in results}
        assert speakers == {"Alice", "Bob"}
        for r in results:
            assert isinstance(r, SentimentResult)

    def test_with_raw_text(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        transcript = MeetingTranscript(
            meeting_id="m1",
            title="Test",
            date=datetime(2025, 1, 1),
            raw_text="[00:00] Alice: Hello everyone\n[00:01] Bob: Good morning",
        )

        results = analyzer.analyze_meeting(transcript)

        assert len(results) == 2
        speakers = {r.speaker for r in results}
        assert speakers == {"Alice", "Bob"}

    def test_empty_turns_returns_empty(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        transcript = MeetingTranscript(
            meeting_id="m1",
            title="Test",
            date=datetime(2025, 1, 1),
        )

        results = analyzer.analyze_meeting(transcript)
        assert results == []


class TestStarMapping:
    """Test that star ratings from the BERT model map correctly to sentiment labels."""

    @pytest.fixture
    def analyzer_with_star(self, mock_sentiment_classifier):
        """Return a factory that creates an analyzer with a specific star rating."""
        def _make(star: int, score: float = 0.8):
            mock_sentiment_classifier.return_value = lambda text, **kw: [
                {"label": f"{star} stars", "score": score}
            ]
            from backend.sentiment import SentimentAnalyzer
            return SentimentAnalyzer()
        return _make

    def test_1_star_negative(self, analyzer_with_star):
        analyzer = analyzer_with_star(1)
        result = analyzer._analyze_speaker("Alice", ["Bad meeting"])
        assert result.overall_sentiment == "negative"

    def test_2_star_negative(self, analyzer_with_star):
        analyzer = analyzer_with_star(2)
        result = analyzer._analyze_speaker("Alice", ["Not great"])
        assert result.overall_sentiment == "negative"

    def test_3_star_neutral(self, analyzer_with_star):
        analyzer = analyzer_with_star(3)
        result = analyzer._analyze_speaker("Alice", ["Okay meeting"])
        assert result.overall_sentiment == "neutral"

    def test_4_star_positive(self, analyzer_with_star):
        analyzer = analyzer_with_star(4)
        result = analyzer._analyze_speaker("Alice", ["Good meeting"])
        assert result.overall_sentiment == "positive"

    def test_5_star_positive(self, analyzer_with_star):
        analyzer = analyzer_with_star(5)
        result = analyzer._analyze_speaker("Alice", ["Excellent meeting"])
        assert result.overall_sentiment == "positive"


class TestTextHandling:
    def test_truncation_at_512_chars(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        long_text = "word " * 200  # >512 chars
        result = analyzer._analyze_speaker("Alice", [long_text])
        assert isinstance(result, SentimentResult)

    def test_max_10_texts_per_speaker(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        texts = [f"Sentence number {i}" for i in range(20)]
        result = analyzer._analyze_speaker("Alice", texts)
        # The analyzer joins texts[:10], so it should still work
        assert isinstance(result, SentimentResult)

    def test_empty_texts_returns_neutral(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        result = analyzer._analyze_speaker("Alice", [])
        assert result.overall_sentiment == "neutral"
        assert result.confidence == 0.0


class TestKeyPhrases:
    def test_extracts_up_to_3_phrases(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        texts = [
            "We need to improve the deployment process significantly",
            "The new feature is working really well now",
            "Database migration went smoothly this time around",
            "Should review the monitoring setup before launch",
        ]
        phrases = analyzer._extract_key_phrases(texts)
        assert len(phrases) <= 3
        assert all(isinstance(p, str) for p in phrases)

    def test_skips_short_texts(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        texts = ["Hi", "Ok", "Yes"]
        phrases = analyzer._extract_key_phrases(texts)
        assert phrases == []


class TestParseRawTranscript:
    def test_valid_format(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        raw = "[00:00] Alice: Hello\n[00:01] Bob: Hi\n[00:02] Alice: Ready?"
        result = analyzer._parse_raw_transcript(raw)
        assert "Alice" in result
        assert "Bob" in result
        assert len(result["Alice"]) == 2

    def test_malformed_lines_gracefully_skipped(self, mock_sentiment_classifier):
        from backend.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        raw = "This is garbage\n---\n[00:00] Alice: Valid line\nAnother bad line"
        result = analyzer._parse_raw_transcript(raw)
        assert "Alice" in result
        assert len(result) == 1
