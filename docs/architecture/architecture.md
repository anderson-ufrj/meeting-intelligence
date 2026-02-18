# Architecture

## System Overview

Meeting Intelligence is a two-tier pipeline that processes Microsoft Teams transcripts into structured, searchable insights. The system is designed around a **privacy-first** architecture where data sensitivity determines the processing path.

![System Overview](../diagrams/system-overview.png)

## High-Level Flow

```mermaid
flowchart TD
    A[/"Microsoft Teams Transcript"/] --> B{"Tier\nClassification"}
    B -->|ordinary| C["LLM Extraction\n(Instructor + Claude)"]
    B -->|sensitive| D["PII Redaction\n(Presidio)"]
    D --> E["LLM Extraction\n(Instructor + Claude)"]
    C --> F["BERT Sentiment\nAnalysis"]
    E --> F
    F --> G[("Redis Vector Store\n(sentence-transformers)")]
    G --> H["Dashboard"]
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

## Components

### 1. Tier Classification

Transcripts are classified at ingestion time into one of two privacy tiers:

| Aspect | Ordinary | Sensitive |
|--------|----------|-----------|
| Use case | Team standups, regular meetings | Executive reviews, HR, M&A |
| PII redaction | None | Automatic (Presidio) |
| Access control | Open | RBAC (restricted) |
| Redis namespace | `ordinary:*` | `sensitive:*` |
| Audit trail | Basic | Full |
| Search scope | Cross-meeting | Tier-isolated |

```python
class TierClassification(str, Enum):
    ORDINARY = "ordinary"
    SENSITIVE = "sensitive"
```

![Tier Comparison](../diagrams/tier-comparison.png)

### 2. PII Redaction (Sensitive Tier Only)

For sensitive meetings, PII is redacted **before** any LLM processing to prevent data leakage to external providers.

```mermaid
flowchart LR
    A["Raw Transcript"] --> B["Presidio Analyzer\n(NER detection)"]
    B --> C["Presidio Anonymizer\n(entity replacement)"]
    C --> D["Redacted Transcript"]

    style B fill:#ffebee,stroke:#c62828
    style C fill:#ffebee,stroke:#c62828
```

**Redacted entity types:**

| Entity | Example | Replacement |
|--------|---------|-------------|
| `PERSON` | John Smith | `<PERSON>` |
| `EMAIL_ADDRESS` | john@acme.com | `<EMAIL_ADDRESS>` |
| `PHONE_NUMBER` | +1-555-0123 | `<PHONE_NUMBER>` |
| `LOCATION` | Oslo, Norway | `<LOCATION>` |
| `CREDIT_CARD` | 4111-1111-... | `<CREDIT_CARD>` |
| `DATE_TIME` | January 15, 2025 | `<DATE_TIME>` |
| `NRP` | Nationality/Religious/Political | `<NRP>` |

**Implementation:** `src/backend/redaction.py` — `PIIRedactor` class using Microsoft Presidio.

### 3. Structured Extraction (LLM)

Uses **Claude Sonnet 4** via the **Instructor** library to extract structured data from transcripts. Instructor enforces Pydantic schema validation with automatic retries.

```mermaid
flowchart LR
    A["Transcript Text"] --> B["Instructor Client\n(Anthropic SDK)"]
    B --> C["Claude Sonnet 4\n(max_tokens: 4096)"]
    C --> D["Pydantic Validation\n(MeetingInsights)"]
    D -->|valid| E["Structured Output"]
    D -->|invalid| B

    style C fill:#e8eaf6,stroke:#283593
    style D fill:#e8f5e9,stroke:#2e7d32
```

**Extracted schema (`MeetingInsights`):**

```
MeetingInsights
├── summary: str                    # Brief meeting overview
├── decisions: List[Decision]       # topic, decision, deciders, confidence
├── action_items: List[ActionItem]  # task, owner, deadline, priority
├── key_topics: List[Topic]         # name, importance, related_speakers
└── open_questions: List[OpenQuestion]  # question, context, stakeholders
```

**Implementation:** `src/backend/extractor.py` — `MeetingExtractor` class.

### 4. Sentiment Analysis

Per-speaker sentiment scoring using a multilingual BERT model (`nlptown/bert-base-multilingual-uncased-sentiment`). The model outputs 1-5 star ratings mapped to sentiment labels.

```mermaid
flowchart LR
    A["Speaker Turns\n(grouped)"] --> B["BERT Classifier\n(1-5 stars)"]
    B --> C{"Star Rating"}
    C -->|"1-2"| D["Negative"]
    C -->|"3"| E["Neutral"]
    C -->|"4-5"| F["Positive"]

    style D fill:#ffebee,stroke:#c62828
    style E fill:#fff8e1,stroke:#f57f17
    style F fill:#e8f5e9,stroke:#2e7d32
```

**Output (`SentimentResult`):**
- `speaker` — participant name
- `overall_sentiment` — positive / neutral / negative
- `confidence` — model confidence (0.0 to 1.0)
- `key_phrases` — representative phrases from the speaker

**Implementation:** `src/backend/sentiment.py` — `SentimentAnalyzer` class.

### 5. Vector Store & Semantic Search

Embeddings are generated locally using **Sentence Transformers** (`all-MiniLM-L6-v2`, 384 dimensions) and stored in **Redis**. Search uses cosine similarity computed in-process (no Redis Stack required).

```mermaid
flowchart TD
    subgraph Indexing
        A["ProcessedMeeting"] --> B["Document Builder\n(summary + decisions + actions)"]
        B --> C["Sentence Transformer\n(all-MiniLM-L6-v2)"]
        C --> D["384-dim Embedding"]
        D --> E[("Redis\n(JSON + embedding)")]
    end

    subgraph Search
        F["User Query"] --> G["Query Embedding"]
        G --> H["Cosine Similarity\n(vs all stored)"]
        H --> I["Ranked Results"]
    end

    E -.-> H

    style C fill:#e3f2fd,stroke:#1565c0
    style E fill:#f3e5f5,stroke:#6a1b9a
    style G fill:#e3f2fd,stroke:#1565c0
```

**Redis key structure:**

| Key Pattern | Content |
|-------------|---------|
| `meeting:{namespace}:{id}` | Full processed meeting (JSON) |
| `emb:{namespace}:{id}` | 384-dim embedding vector (JSON) |
| `idx:{namespace}` | Set of all meeting IDs in namespace |
| `transcript:{namespace}:{id}` | Raw transcript text |

**Implementation:** `src/backend/vectorstore.py` — `MeetingVectorStore` class.

## Pipeline Orchestration

The `MeetingPipeline` class (`src/backend/pipeline.py`) coordinates all components:

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant P as Pipeline
    participant R as PIIRedactor
    participant E as MeetingExtractor
    participant S as SentimentAnalyzer
    participant V as VectorStore

    API->>P: process(transcript)

    alt Sensitive Tier
        P->>R: redact_transcript(text)
        R-->>P: RedactionResult
        Note over P: Replace transcript with redacted version
    end

    P->>E: extract(transcript)
    E-->>P: MeetingInsights

    P->>S: analyze_meeting(transcript)
    S-->>P: List[SentimentResult]

    P->>V: add_meeting(processed)
    V-->>P: vector_id

    P-->>API: ProcessedMeeting
```

Each step appends to the `audit_log` with timestamps, enabling full traceability.

## API Layer

FastAPI REST API with 7 endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check (redis status, version) |
| `POST` | `/api/v1/meetings/process` | Submit transcript for processing |
| `GET` | `/api/v1/meetings/search` | Semantic search across meetings |
| `GET` | `/api/v1/meetings` | List meetings by tier |
| `GET` | `/api/v1/meetings/{id}` | Get meeting insights |
| `GET` | `/api/v1/meetings/{id}/transcript` | Get raw transcript |
| `DELETE` | `/api/v1/meetings/{id}` | Delete meeting data |

Interactive docs available at [`/docs`](https://meeting-intelligence-api-production.up.railway.app/docs) (Swagger) and [`/redoc`](https://meeting-intelligence-api-production.up.railway.app/redoc) (ReDoc).

## Frontend

Next.js 15 dashboard with App Router, shadcn/ui components, and dark/light theme support.

| Route | Purpose |
|-------|---------|
| `/` | Upload transcript for processing |
| `/dashboard` | Analytics and insights overview |
| `/meetings` | Meeting list with tier filtering |
| `/meetings/[id]` | Full meeting detail view |
| `/search` | Semantic search interface |

## Deployment Architecture

```mermaid
flowchart LR
    subgraph Railway
        BE["Backend\n(FastAPI)\nPort 8000"]
        FE["Frontend\n(Next.js)\nPort 3000"]
        RD[("Redis\n(native plugin)")]
    end

    U["User"] --> FE
    FE -->|"/api/[...path]"| BE
    BE --> RD

    style BE fill:#e8f5e9,stroke:#2e7d32
    style FE fill:#e3f2fd,stroke:#1565c0
    style RD fill:#f3e5f5,stroke:#6a1b9a
```

Three Railway services:
- **Backend** — Python 3.11 Docker container (FastAPI + Uvicorn)
- **Frontend** — Next.js 15 with API proxy route (`/api/[...path]`)
- **Redis** — Railway native plugin (persistent)

## Data Models

```mermaid
classDiagram
    class MeetingTranscript {
        +str meeting_id
        +str title
        +datetime date
        +TierClassification tier
        +List~Speaker~ participants
        +List~DialogueTurn~ turns
        +str raw_text
    }

    class ProcessedMeeting {
        +str meeting_id
        +TierClassification tier
        +MeetingInsights insights
        +List~SentimentResult~ sentiments
        +str vector_id
        +datetime processed_at
        +List~dict~ audit_log
    }

    class MeetingInsights {
        +str summary
        +List~Decision~ decisions
        +List~ActionItem~ action_items
        +List~Topic~ key_topics
        +List~OpenQuestion~ open_questions
    }

    class Decision {
        +str topic
        +str decision
        +List~str~ deciders
        +float confidence
    }

    class ActionItem {
        +str task
        +str owner
        +str deadline
        +str priority
    }

    class SentimentResult {
        +str speaker
        +str overall_sentiment
        +float confidence
        +List~str~ key_phrases
    }

    MeetingTranscript --> ProcessedMeeting : pipeline.process()
    ProcessedMeeting --> MeetingInsights
    ProcessedMeeting --> SentimentResult
    MeetingInsights --> Decision
    MeetingInsights --> ActionItem
```

## Design Decisions

See [ADR-001: Two-Tier Privacy Model](../decisions/adr-001-two-tier-model.md) for the rationale behind the binary tier classification.

Key trade-offs:
- **Pre-processing redaction** (not post-processing) — prevents PII from reaching the LLM provider
- **Local embeddings** (sentence-transformers) — no external API dependency for vectorization
- **In-process cosine similarity** — works with standard Redis (no Redis Stack required)
- **Binary tier model** — simplicity over granularity for initial implementation
