# Meeting Intelligence

Two-tier meeting intelligence pipeline for Microsoft Teams transcripts.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEETING INTELLIGENCE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐  │
│  │    Input     │ ───► │    Tier      │ ───► │   Correct Pipeline   │  │
│  │  Transcript  │      │ Classification      │                      │  │
│  │    Teams     │      │ (Ord/Sens)   │      ├──────────┬───────────┤  │
│  └──────────────┘      └──────────────┘      │          │           │  │
│                                              │ Ordinary │ Sensitive │  │
│                                              │          │           │  │
│                                              ▼          ▼           │  │
│                                         ┌─────────┐  ┌──────────┐  │  │
│                                         │  LLM    │  │  PII     │  │  │
│                                         │Extract  │  │Redaction │  │  │
│                                         │(Instructor) ├──────────┤  │  │
│                                         │         │  │  LLM     │  │  │
│                                         │         │  │ Extract  │  │  │
│                                         └────┬────┘  └────┬─────┘  │  │
│                                              │            │        │  │
│                                              └─────┬──────┘        │  │
│                                                    ▼                │  │
│                                           ┌─────────────┐           │  │
│                                           │  Sentiment  │           │  │
│                                           │   (BERT)    │           │  │
│                                           └──────┬──────┘           │  │
│                                                  ▼                  │  │
│                                           ┌─────────────┐           │  │
│                                           │    Redis    │           │  │
│                                           │  (vectors)  │           │  │
│                                           └──────┬──────┘           │  │
│                                                  ▼                  │  │
│                                           ┌─────────────┐           │  │
│                                           │   Semantic  │           │  │
│                                           │    Search   │           │  │
│                                           │    (RAG)    │           │  │
│                                           └─────────────┘           │  │
│                                                                     │  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Privacy Tiers

| Feature | Ordinary Tier | Sensitive Tier |
|---------|---------------|----------------|
| PII Redaction | No | Yes |
| Access | Open | Restricted |
| Audit | Basic | Full |
| Redis Namespace | `ordinary:*` | `sensitive:*` |

## Stack

| Layer | Technology |
|-------|-----------|
| LLM Extraction | Instructor + Pydantic + OpenAI |
| Sentiment | BERT (transformers) |
| PII Redaction | Microsoft Presidio |
| Vector Store | Redis + OpenAI Embeddings |
| API | FastAPI |
| Frontend | Next.js 15 + shadcn/ui |
| Deploy | Railway |

## Installation

```bash
pip install -e ".[dev]"
python -m spacy download en_core_web_lg
```

## Configuration

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379
```

## Project Structure

```
meeting-intelligence/
├── src/meeting_intelligence/    # Backend (Python)
│   ├── models.py               # Pydantic schemas
│   ├── extractor.py            # Instructor extraction
│   ├── sentiment.py            # BERT analysis
│   ├── vectorstore.py          # Redis + embeddings
│   ├── pipeline.py             # Orchestrator
│   ├── redaction.py            # PII redaction
│   └── api.py                  # FastAPI application
├── frontend/                    # Dashboard (Next.js)
├── examples/                    # Transcript samples
│   ├── ordinary/               # Ordinary tier examples
│   └── sensitive/              # Sensitive tier examples
├── docs/                        # Documentation
│   ├── architecture/           # D2 diagrams
│   ├── features/               # Feature specs
│   ├── api/                    # API specification
│   ├── deployment/             # Railway deployment
│   └── decisions/              # ADRs
├── Dockerfile                   # Backend container
└── pyproject.toml              # Python config
```

## Deployment

Both backend and frontend deploy to Railway with a shared Redis instance:

```bash
# Backend: FastAPI on port 8000
# Frontend: Next.js on port 3000
# Redis: Railway native plugin
```

## Context

Architecture demonstration for StormGeo — meeting insight extraction for the CST Shipping division.
