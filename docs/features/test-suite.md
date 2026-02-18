# Test Suite — Roadmap

## Problem

The Meeting Intelligence backend has 8 Python modules (`models`, `extractor`, `sentiment`, `redaction`, `vectorstore`, `pipeline`, `api`, `__init__`) with zero test coverage. For a PoC being presented to StormGeo stakeholders, this is a critical gap. Without tests, regressions go undetected, refactoring is risky, and engineering maturity is hard to demonstrate.

## Proposed Solution

A comprehensive pytest suite targeting ~80% coverage across all backend modules. Tests are fast and fully isolated — no real API calls, no model loading, no Redis connections. All external dependencies are mocked.

## Test Architecture

```
tests/
├── conftest.py              # Shared fixtures (mock pipeline, redis, sample data)
├── test_models.py           # Pydantic schema validation
├── test_extractor.py        # LLM extraction (mocked Anthropic)
├── test_sentiment.py        # BERT sentiment (mocked transformers)
├── test_redaction.py        # PII redaction (mocked Presidio)
├── test_vectorstore.py      # Redis vector store (mocked Redis)
├── test_pipeline.py         # Pipeline orchestration (all mocked)
└── test_api.py              # FastAPI endpoints (TestClient)
```

## Dependencies

```toml
# pyproject.toml [project.optional-dependencies] dev
fakeredis >= 2.20.0    # In-memory Redis mock
httpx >= 0.25.0        # Required by FastAPI TestClient
pytest-cov >= 4.1.0    # Coverage reporting
```

## Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v --tb=short"
```

## Implementation Phases

### Phase 1 — Infrastructure & Models (~15 tests)

Shared fixtures in `conftest.py` and Pydantic model validation in `test_models.py`. No mocking needed — pure data validation.

**conftest.py fixtures:**

- `sample_transcript` — MeetingTranscript with 3 speakers, 6 turns
- `sample_sensitive_transcript` — Same but tier=SENSITIVE, includes PII
- `sample_insights` — MeetingInsights with decisions, actions, topics
- `sample_processed_meeting` — Full ProcessedMeeting with sentiments
- `mock_redis` — Patched `redis.from_url` returning MagicMock
- `mock_anthropic` — Patched instructor client returning sample_insights

**test_models.py tests:**

| Test | What it validates |
|------|-------------------|
| `test_tier_classification_values` | Enum has "ordinary" and "sensitive" |
| `test_decision_confidence_bounds` | 0.0-1.0 range enforced by Pydantic |
| `test_meeting_insights_defaults` | Empty lists for optional fields |
| `test_meeting_transcript_defaults` | tier=ORDINARY, empty participants |
| `test_processed_meeting_auto_timestamp` | processed_at auto-populated |
| `test_sentiment_result_valid` | All fields serialize correctly |
| `test_action_item_optional_fields` | deadline/priority can be None |
| `test_speaker_optional_fields` | email/role can be None |
| `test_topic_importance_values` | Accepts high/medium/low strings |
| `test_transcript_with_raw_text_only` | Works without turns |
| `test_transcript_with_turns_only` | Works without raw_text |
| `test_decision_serialization` | JSON round-trip preserves data |
| `test_open_question_model` | question + context required |
| `test_invalid_confidence_rejected` | Values >1.0 or <0.0 raise error |
| `test_process_request_validation` | title min/max, transcript min, tier pattern |

**Effort**: ~1 hour

### Phase 2 — Core Modules (~28 tests)

Tests for the three core processing modules: LLM extraction, sentiment analysis, and PII redaction. All external services mocked via `unittest.mock.patch`.

**test_extractor.py (~8 tests):**

| Test | What it validates |
|------|-------------------|
| `test_init_with_api_key` | Accepts explicit key |
| `test_init_from_env` | Reads ANTHROPIC_API_KEY from env |
| `test_init_no_key_raises` | ValueError if no key available |
| `test_extract_returns_insights` | Mocked client returns MeetingInsights |
| `test_build_context_with_turns` | Formats "[timestamp] speaker: text" |
| `test_build_context_with_raw_text` | Falls back to raw_text |
| `test_build_context_includes_participants` | Lists participants in prompt |
| `test_extract_sets_title_and_date` | Overwrites title/date on result |

Mocking: `unittest.mock.patch` on `instructor.from_anthropic` and `anthropic.Anthropic`

**test_sentiment.py (~10 tests):**

| Test | What it validates |
|------|-------------------|
| `test_analyze_meeting_with_turns` | Groups by speaker, returns SentimentResult per speaker |
| `test_analyze_meeting_with_raw_text` | Parses raw transcript format |
| `test_star_mapping_negative` | 1-2 stars -> "negative" |
| `test_star_mapping_neutral` | 3 stars -> "neutral" |
| `test_star_mapping_positive` | 4-5 stars -> "positive" |
| `test_text_truncation` | Texts >512 chars truncated |
| `test_max_10_texts_per_speaker` | Only first 10 texts used |
| `test_key_phrases_extraction` | Returns up to 3 phrases, >3 words each |
| `test_empty_turns_returns_empty` | No turns + no raw_text -> [] |
| `test_parse_raw_transcript_malformed` | Gracefully handles bad lines |

Mocking: `unittest.mock.patch` on `transformers.pipeline` returning fake classifier

**test_redaction.py (~10 tests):**

| Test | What it validates |
|------|-------------------|
| `test_redact_detects_email` | Replaces email with `<EMAIL_ADDRESS>` |
| `test_redact_detects_phone` | Replaces phone with `<PHONE_NUMBER>` |
| `test_redact_no_entities` | Returns original text, count=0 |
| `test_redact_multiple_entities` | Handles multiple PII types |
| `test_redact_transcript_preserves_speakers` | Speaker names restored after redaction |
| `test_redact_transcript_without_preservation` | Full redaction without speaker list |
| `test_audit_log_entry_format` | Correct keys: timestamp, action, entities |
| `test_default_entity_list` | All 8 default entities present |
| `test_custom_entity_list` | Can override entities to detect |
| `test_simple_redact_fallback` | Regex-based redaction works |

Mocking: `unittest.mock.patch` on `AnalyzerEngine` and `AnonymizerEngine`

**Effort**: ~2 hours

### Phase 3 — Integration Layer (~22 tests)

Tests for the Redis vector store and pipeline orchestration. All components mocked to test wiring and data flow.

**test_vectorstore.py (~12 tests):**

| Test | What it validates |
|------|-------------------|
| `test_key_generation` | Correct namespace prefixes |
| `test_add_meeting` | Stores data + embedding in Redis |
| `test_get_meeting_found` | Returns parsed meeting data |
| `test_get_meeting_not_found` | Returns None |
| `test_list_meetings` | Returns sorted metadata list |
| `test_list_meetings_empty` | Empty namespace returns [] |
| `test_delete_meeting` | Removes data, embedding, and index entry |
| `test_search_returns_ranked` | Results sorted by score desc |
| `test_search_empty_namespace` | Returns [] |
| `test_cosine_similarity_identical` | Score ~1.0 for same vector |
| `test_cosine_similarity_zero_norm` | Returns 0.0 gracefully |
| `test_create_tiered_stores` | Returns dict with "ordinary" and "sensitive" |

Mocking: `fakeredis` or `unittest.mock.patch` on `redis.from_url`; patch `SentenceTransformer`

**test_pipeline.py (~10 tests):**

| Test | What it validates |
|------|-------------------|
| `test_process_ordinary_skips_redaction` | No redactor called for ordinary tier |
| `test_process_sensitive_applies_redaction` | Redactor called, redacted text used |
| `test_process_calls_extractor` | extractor.extract() invoked |
| `test_process_calls_sentiment` | sentiment_analyzer.analyze_meeting() invoked |
| `test_process_stores_in_vectordb` | store.add_meeting() invoked with correct tier |
| `test_process_returns_processed_meeting` | Has all fields: insights, sentiments, vector_id |
| `test_audit_log_has_all_steps` | 4+ entries in audit_log |
| `test_process_with_redaction_disabled` | enable_redaction=False skips PIIRedactor init |
| `test_search_meetings_with_tier` | Searches correct store |
| `test_search_meetings_default_ordinary` | No tier -> searches ordinary |

Mocking: Patch all 4 components (extractor, sentiment, redactor, vectorstore)

**Effort**: ~1.5 hours

### Phase 4 — API Endpoints (~15 tests)

End-to-end endpoint tests using FastAPI `TestClient` with the entire pipeline mocked.

**test_api.py:**

| Test | What it validates |
|------|-------------------|
| `test_health_redis_connected` | Returns status="healthy" |
| `test_health_redis_disconnected` | Returns status="degraded" |
| `test_process_meeting_success` | 200 + insights in response |
| `test_process_meeting_auto_id` | Generates meeting_id if not provided |
| `test_process_meeting_invalid_tier` | 400 for unknown tier |
| `test_process_meeting_short_transcript` | 422 for transcript <10 chars |
| `test_process_pipeline_not_ready` | 503 if pipeline is None |
| `test_list_meetings` | Returns meetings array |
| `test_get_meeting_found` | Returns meeting data |
| `test_get_meeting_not_found` | 404 |
| `test_get_transcript_found` | Returns raw transcript |
| `test_get_transcript_not_found` | 404 |
| `test_search_meetings` | Returns query + results |
| `test_delete_meeting` | Returns status="deleted" |
| `test_stats_aggregation` | Returns correct totals |

Mocking: Override `pipeline` global via dependency injection or direct patching

**Effort**: ~1.5 hours

## Verification Commands

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=backend --cov-report=term-missing

# Single module (fast, no mocks)
pytest tests/test_models.py -v

# Stop on first failure
pytest tests/ -x
```

## Summary

| Phase | Files | Tests | Effort |
|-------|-------|-------|--------|
| 1 — Infrastructure & Models | conftest.py, test_models.py | ~15 | ~1h |
| 2 — Core Modules | test_extractor.py, test_sentiment.py, test_redaction.py | ~28 | ~2h |
| 3 — Integration Layer | test_vectorstore.py, test_pipeline.py | ~22 | ~1.5h |
| 4 — API Endpoints | test_api.py | ~15 | ~1.5h |
| **Total** | **8 files** | **~80 tests** | **~6h** |

## Success Metrics

- 80%+ line coverage across all backend modules
- All tests passing with zero real API/model calls
- Full test run completes in under 30 seconds

## Priority

**High** — Zero test coverage on a PoC being presented to stakeholders is a credibility risk. Tests validate pipeline correctness, catch regressions during rapid iteration, and demonstrate engineering maturity.
