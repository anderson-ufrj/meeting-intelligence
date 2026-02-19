# Test Suite

Comprehensive three-layer test suite for the Meeting Intelligence platform. Covers backend (Python/FastAPI), frontend (Next.js/TypeScript), and end-to-end pipeline flows.

## Overview

| Metric | Value |
|--------|-------|
| **Total Tests** | 165 (149 backend + 16 frontend) |
| **Backend Coverage** | 92% |
| **Execution Time** | ~28s backend, ~0.3s frontend |
| **External Calls** | Zero (all mocked) |

## Architecture

```
tests/
├── unit/
│   └── backend/             # 114 tests — isolated module logic
│       ├── conftest.py      # Shared fixtures (sample data, mock helpers)
│       ├── test_models.py   # Pydantic schema validation (29 tests)
│       ├── test_extractor.py    # LLM extraction, mocked Anthropic (9 tests)
│       ├── test_sentiment.py    # BERT sentiment, mocked transformers (16 tests)
│       ├── test_redaction.py    # PII redaction, mocked Presidio (15 tests)
│       ├── test_vectorstore.py  # Redis vector store, mocked Redis (18 tests)
│       ├── test_pipeline.py     # Pipeline orchestration, all mocked (12 tests)
│       └── test_api.py          # FastAPI endpoints, TestClient (15 tests)
│
├── smoke/                   # 27 tests — system responsiveness
│   ├── conftest.py          # Module-scoped TestClient + mock pipeline
│   └── test_backend_smoke.py    # All endpoints: status codes, schemas, CORS, OpenAPI
│
└── e2e/                     # 8 tests — full pipeline flows
    ├── conftest.py          # fakeredis server + mock LLM/BERT/Presidio
    └── test_full_pipeline.py    # Process → store → search → delete (both tiers)

src/frontend/__tests__/
├── setup.ts             # Vitest + jest-dom setup
├── smoke.test.ts        # Module exports, utility functions (3 tests)
└── lib/
    └── api.test.ts      # API client functions, mocked fetch (13 tests)
```

## Test Layers

### Unit Tests (114 tests, ~0.3s)

Isolated logic tests with all external dependencies mocked. Each module tested independently.

| File | Tests | What it validates |
|------|-------|-------------------|
| `test_models.py` | 29 | Pydantic field validation, defaults, confidence bounds, serialization, enum behavior |
| `test_extractor.py` | 9 | Init with/without API key, context building (turns/raw/participants), extract returns |
| `test_sentiment.py` | 16 | Star-to-label mapping (1-5), text truncation, key phrase extraction, raw text parsing |
| `test_redaction.py` | 15 | Entity detection (email/phone/SSN), audit log format, speaker preservation, regex fallback |
| `test_vectorstore.py` | 18 | Key generation, CRUD operations, cosine similarity, ranked search, tiered stores |
| `test_pipeline.py` | 12 | Ordinary/sensitive flow, redaction skipping, audit log, search delegation |
| `test_api.py` | 15 | All endpoints via TestClient, validation errors, 404/503 handling |

### Smoke Tests (27 tests, ~1s)

Verify all endpoints respond with correct HTTP status codes and response schemas. Uses a module-scoped mock pipeline for speed.

**What they catch:**
- Broken imports or missing dependencies
- Schema changes that break API contracts
- Missing required response fields
- CORS misconfiguration
- OpenAPI spec generation errors

### E2E Tests (8 tests, ~28s)

Full pipeline execution with **fakeredis** (real Redis protocol, in-memory) and mocked LLM/BERT. Tests the complete data flow without any external services.

**Flows tested:**
- Ordinary: process → store → list → search → retrieve → delete
- Sensitive: process with redaction → store in separate namespace → verify isolation
- API layer: full CRUD through FastAPI TestClient with real pipeline wiring

### Frontend Tests (16 tests, ~0.3s)

Vitest with happy-dom. Tests the API client (`lib/api.ts`) with mocked `fetch` and verifies module exports.

| File | Tests | What it validates |
|------|-------|-------------------|
| `api.test.ts` | 13 | Correct URL construction, HTTP methods, error handling, tier parameters |
| `smoke.test.ts` | 3 | Module exports, `cn()` utility, tailwind-merge behavior |

## Coverage Report

| Module | Coverage | Missing |
|--------|----------|---------|
| `models.py` | 100% | — |
| `redaction.py` | 100% | — |
| `__init__.py` | 100% | — |
| `vectorstore.py` | 97% | `cross_meeting_search` |
| `sentiment.py` | 93% | `analyze_sentiment_simple` convenience fn |
| `extractor.py` | 87% | `extract_meeting_insights` convenience fn |
| `pipeline.py` | 87% | `quick_process` convenience fn |
| `api.py` | 86% | Lifespan init, some error branches in dedup |
| **Total** | **92%** | |

## Mocking Strategy

All external services are mocked to ensure tests are fast, deterministic, and require no credentials or infrastructure.

| Dependency | Mock Method | Used In |
|------------|-------------|---------|
| Anthropic Claude API | `unittest.mock.patch` on `instructor.from_anthropic` | Unit, E2E |
| HuggingFace Transformers | `unittest.mock.patch` on `transformers.pipeline` | Unit, E2E |
| Microsoft Presidio | `unittest.mock.patch` on `AnalyzerEngine`/`AnonymizerEngine` | Unit, E2E |
| Redis | `unittest.mock.MagicMock` (unit), `fakeredis.FakeRedis` (e2e) | All layers |
| SentenceTransformer | `unittest.mock.patch` with numpy random vectors | Unit, E2E |

## Commands

```bash
# Backend — full suite
pytest tests/ -v

# Backend — by layer
pytest tests/unit/ -v              # Unit only
pytest tests/smoke/ -v -m smoke    # Smoke only
pytest tests/e2e/ -v -m e2e       # E2E only

# Backend — with coverage
pytest tests/ --cov=backend --cov-report=term-missing

# Backend — single module (fast iteration)
pytest tests/unit/backend/test_models.py -v

# Frontend — full suite
cd src/frontend && npm test

# Frontend — watch mode
cd src/frontend && npm run test:watch
```

## Dependencies

### Backend (pyproject.toml `[dev]`)

```
pytest >= 7.4.0
pytest-cov >= 4.1.0
fakeredis >= 2.20.0
httpx >= 0.25.0
```

### Frontend (package.json `devDependencies`)

```
vitest
@vitejs/plugin-react
@testing-library/react
@testing-library/jest-dom
happy-dom
```
