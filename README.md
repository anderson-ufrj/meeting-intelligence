# Meeting Intelligence

Two-tier meeting intelligence pipeline for Microsoft Teams transcripts. Extracts structured insights, performs per-speaker sentiment analysis, and enables semantic search — with automatic PII redaction for sensitive content.

**Live:** [Frontend](https://meeting-intelligence-production.up.railway.app/) | [API Docs](https://meeting-intelligence-api-production.up.railway.app/docs)

## Architecture

```mermaid
flowchart TD
    A[/"Microsoft Teams\nTranscript"/] --> B{"Tier\nClassification"}
    B -->|ordinary| C["LLM Extraction\n(Instructor + Claude)"]
    B -->|sensitive| D["PII Redaction\n(Presidio)"]
    D --> E["LLM Extraction\n(Instructor + Claude)"]
    C --> F["BERT Sentiment\nAnalysis"]
    E --> F
    F --> G[("Redis Vector Store\n(sentence-transformers)")]
    G --> H["Next.js Dashboard"]
    G --> I["Semantic Search\n(RAG)"]
    G -.->|sensitive only| J[("Audit Trail")]

    style B fill:#fff3e0,stroke:#f57f17
    style C fill:#e8f5e9,stroke:#2e7d32
    style D fill:#ffebee,stroke:#c62828
    style E fill:#ffebee,stroke:#c62828
    style F fill:#e3f2fd,stroke:#1565c0
    style G fill:#f3e5f5,stroke:#6a1b9a
    style J fill:#fce4ec,stroke:#c62828
```

> Detailed architecture, D2 diagrams, sequence diagrams, and data models in [`docs/architecture/`](docs/architecture/architecture.md).

## Stack

| Layer | Technology |
|-------|-----------|
| LLM Extraction | Claude Sonnet 4 + Instructor + Pydantic 2 |
| Sentiment | BERT multilingual (per-speaker) |
| PII Redaction | Microsoft Presidio |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2, local) |
| Vector Store | Redis (cosine similarity) |
| API | FastAPI |
| Frontend | Next.js 15 + shadcn/ui |
| Deploy | Railway (3 services) |

## Privacy Tiers

| Feature | Ordinary | Sensitive |
|---------|----------|-----------|
| PII Redaction | No | Yes (Presidio) |
| Access | Open | RBAC |
| Audit | Basic | Full |
| Redis Namespace | `ordinary:*` | `sensitive:*` |

## Quick Start

```bash
# Backend
pip install -e ".[dev]"
python -m spacy download en_core_web_lg
cp .env.example .env   # set ANTHROPIC_API_KEY and REDIS_URL
uvicorn backend.api:app --reload

# Frontend
cd src/frontend && npm install && npm run dev
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/meetings/process` | Process transcript |
| `GET` | `/api/v1/meetings/search?q=...` | Semantic search |
| `GET` | `/api/v1/meetings` | List meetings |
| `GET` | `/api/v1/meetings/{id}` | Get meeting insights |
| `DELETE` | `/api/v1/meetings/{id}` | Delete meeting |

Full reference: [`docs/api/endpoints.md`](docs/api/endpoints.md) | Interactive: [`/docs`](https://meeting-intelligence-api-production.up.railway.app/docs)

## Deployment

Three Railway services:
- **Backend** — FastAPI (Docker, Python 3.11) — [API Docs](https://meeting-intelligence-api-production.up.railway.app/docs)
- **Frontend** — Next.js 15 — [Live](https://meeting-intelligence-production.up.railway.app/)
- **Redis** — Railway native plugin

Guide: [`docs/deployment/railway-setup.md`](docs/deployment/railway-setup.md)

## Docs

| | |
|---|---|
| [Architecture](docs/architecture/architecture.md) | System design, diagrams, data models |
| [ADR-001: Two-Tier Model](docs/decisions/adr-001-two-tier-model.md) | Privacy architecture decision |
| [Privacy Tiers](docs/features/privacy-tiers.md) | Tier behavior and PII entities |
| [Structured Extraction](docs/features/structured-extraction.md) | LLM extraction with Instructor |
| [Sentiment Analysis](docs/features/sentiment-analysis.md) | BERT per-speaker analysis |
| [Semantic Search](docs/features/semantic-search.md) | RAG and vector search |
