# Structured Extraction with Instructor

## Overview

We use [Instructor](https://github.com/jxnl/instructor) with Pydantic models to extract structured insights from meeting transcripts. This approach eliminates hallucinations by enforcing a strict schema on the LLM output.

## Why Instructor + Pydantic?

1. **Type Safety**: All outputs are validated Pydantic models
2. **No Hallucinations**: Schema enforcement prevents made-up fields
3. **Retry Logic**: Automatic retries on validation failures
4. **OpenAI / Azure OpenAI Compatible**: Works with StormGeo's stack

## Extraction Schema

```python
class MeetingInsights(BaseModel):
    meeting_title: str
    meeting_date: Optional[str]
    summary: str
    decisions: List[Decision]
    action_items: List[ActionItem]
    key_topics: List[Topic]
    open_questions: List[OpenQuestion]
```

## Example Usage

```python
from backend import MeetingPipeline
from backend.models import MeetingTranscript

# Create transcript
transcript = MeetingTranscript(
    meeting_id="meeting_001",
    title="Weekly Standup",
    raw_text="[00:00] John: Let's decide on the API design..."
)

# Process
pipeline = MeetingPipeline()
result = pipeline.process(transcript)

# Access structured data
for decision in result.insights.decisions:
    print(f"{decision.topic}: {decision.decision}")

for action in result.insights.action_items:
    print(f"{action.owner} must {action.task} by {action.deadline}")
```

## Validation Rules

The schema enforces:

- `confidence` scores between 0.0 and 1.0
- Non-empty required fields
- Proper date formats
- Valid sentiment labels

## Error Handling

Instructor provides automatic retries (up to 3 attempts) when the LLM returns invalid JSON or violates schema constraints.
