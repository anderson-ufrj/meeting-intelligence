# Sentiment Analysis with BERT

## Overview

Per-speaker sentiment analysis using transformer models. Unlike simple text-level sentiment, we track how each participant's sentiment evolves throughout the meeting.

## Model

We use `nlptown/bert-base-multilingual-uncased-sentiment`:

- **5-star scale**: 1 (very negative) to 5 (very positive)
- **Multilingual**: Supports English, Norwegian, and other languages
- **Fine-tuned**: Specifically for sentiment classification

## Output Format

```python
class SentimentResult(BaseModel):
    speaker: str
    overall_sentiment: str  # positive / neutral / negative
    confidence: float       # 0.0 to 1.0
    key_phrases: List[str]  # Representative phrases
```

## Use Cases

1. **Meeting Health**: Detect negative sentiment trends
2. **Conflict Detection**: Identify tension between speakers
3. **Engagement Analysis**: Track participation quality

## Example

```python
from backend.sentiment import SentimentAnalyzer

analyzer = SentimentAnalyzer()
results = analyzer.analyze_meeting(transcript)

for r in results:
    print(f"{r.speaker}: {r.overall_sentiment} ({r.confidence:.2f})")
    # Output: "John: positive (0.87)"
```

## Limitations

- Analysis based on text only (no tone/voice)
- Context window limits (512 tokens per analysis)
- Sarcasm and nuance may be missed
