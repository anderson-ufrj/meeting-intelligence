# ADR-001: Two-Tier Privacy Model

## Status

**Accepted**

## Context

StormGeo processes meeting transcripts with varying sensitivity levels:
- Regular team standups (low sensitivity)
- Executive reviews (high sensitivity, PII)
- HR discussions (high sensitivity, GDPR-relevant)

We need a privacy architecture that:
1. Protects sensitive data automatically
2. Maintains searchability for ordinary meetings
3. Provides audit trails for compliance
4. Is simple to operate

## Decision

We will implement a **Two-Tier Privacy Model**:

| Tier | Description | Redaction | Access |
|------|-------------|-----------|--------|
| **Ordinary** | Regular meetings | None | Open |
| **Sensitive** | Executive, HR, M&A | PII auto-redacted | RBAC |

## Consequences

### Positive

- Simple mental model (binary choice)
- Automatic PII protection for sensitive content
- Clear audit boundary
- Easy to explain to users

### Negative

- Binary classification may miss edge cases
- Requires upfront tier assignment
- Two separate Redis namespaces to maintain

## Alternatives Considered

### Granular Classification (Rejected)

Multiple levels (Public, Internal, Confidential, Secret) - too complex for initial implementation.

### Post-Processing Redaction (Rejected)

Redacting after LLM processing - leaks PII to LLM provider, violating privacy requirements.

## Implementation

```python
class TierClassification(str, Enum):
    ORDINARY = "ordinary"
    SENSITIVE = "sensitive"
```

Tier is set at ingestion and determines:
1. Whether PII redaction runs
2. Which Redis namespace is used
3. Access control requirements

## References

- [Presidio PII Detection](https://microsoft.github.io/presidio/)
- [GDPR Article 32](https://gdpr.eu/article-32-security-of-processing/)
