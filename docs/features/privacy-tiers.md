# Privacy Tiers

## Two-Tier Model

The system implements a two-tier privacy model based on StormGeo's data classification requirements.

## Ordinary Tier

**Characteristics:**
- Regular team meetings
- No PII redaction
- Open dashboard access
- Shared Redis namespace

**Processing Flow:**
```
Transcript → LLM Extraction → Sentiment → Redis
```

**Access:** Any authenticated user can search and view.

## Sensitive Tier

**Characteristics:**
- Executive meetings
- M&A discussions
- HR matters
- PII automatically redacted

**Processing Flow:**
```
Transcript → PII Redaction → LLM Extraction → Sentiment → Isolated Redis → Audit Log
```

**Access:** Role-based access control (RBAC) required.

## Automatic Classification

```python
class TierClassification(str, Enum):
    ORDINARY = "ordinary"
    SENSITIVE = "sensitive"

# Set at transcript creation
transcript = MeetingTranscript(
    ...,
    tier=TierClassification.SENSITIVE
)
```

## PII Redaction Details

Entities redacted in sensitive tier:

| Entity Type | Example | Redacted To |
|-------------|---------|-------------|
| PERSON | John Smith | `<PERSON>` |
| EMAIL | john@example.com | `<EMAIL_ADDRESS>` |
| PHONE | +1-555-123-4567 | `<PHONE_NUMBER>` |
| LOCATION | New York | `<LOCATION>` |
| ORGANIZATION | Company Name | `<ORGANIZATION>` |

## Audit Trail

Every access to sensitive tier data is logged:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "meeting_id": "exec_001",
  "action": "search",
  "user": "user@stormgeo.com",
  "query": "quarterly results"
}
```
