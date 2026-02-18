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

## Project Structure

```
meeting-intelligence/
├── src/
│   ├── backend/                 # Python API
│   │   ├── api.py               # FastAPI application
│   │   ├── models.py            # Pydantic schemas
│   │   ├── extractor.py         # Instructor extraction
│   │   ├── sentiment.py         # BERT analysis
│   │   ├── vectorstore.py       # Redis + embeddings
│   │   ├── pipeline.py          # Orchestrator
│   │   └── redaction.py         # PII redaction
│   └── frontend/                # Next.js dashboard
│       ├── app/                 # App Router pages
│       ├── components/          # UI components
│       └── package.json
├── examples/                    # Transcript samples
├── docs/                        # Documentation
├── Dockerfile                   # Backend container
└── pyproject.toml               # Python config
```

## Quick Start

```bash
# Backend
pip install -e ".[dev]"
python -m spacy download en_core_web_lg
uvicorn backend.api:app --reload

# Frontend
cd src/frontend
npm install && npm run dev
```

## Configuration

```bash
# .env
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379
```

## Deployment

Three services on Railway:
- **Backend** — FastAPI on port 8000
- **Frontend** — Next.js on port 3000
- **Redis** — Railway native plugin

## Context

Architecture demonstration for StormGeo — meeting insight extraction for the CST Shipping division.
