# Semantic Search & RAG

## Overview

Vector-based semantic search across meeting history using Redis and OpenAI embeddings. Unlike keyword search, this finds conceptually related content even with different terminology.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Query     │────►│   OpenAI    │────►│    Redis    │────►│   Results   │
│  (natural   │     │  Embedding  │     │  (cosine    │     │  (ranked    │
│  language)  │     │  3-small    │     │  similarity)│     │   by score) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## How It Works

1. **Ingestion**: Each processed meeting is converted to a searchable document, embedded via `text-embedding-3-small` (1536 dims), and stored in Redis alongside the full meeting data.
2. **Search**: The query is embedded with the same model. Cosine similarity is computed against all stored embeddings in the target namespace.
3. **Ranking**: Results are sorted by similarity score and returned with metadata.

## Tier Isolation

```python
# Separate Redis namespaces for privacy tiers
stores = {
    "ordinary": MeetingVectorStore(namespace="ordinary"),
    "sensitive": MeetingVectorStore(namespace="sensitive"),
}

# Redis key pattern:
#   meeting:ordinary:{id}   — meeting data
#   emb:ordinary:{id}       — embedding vector
#   idx:ordinary             — set of meeting IDs
```

## Search Examples

```python
# Simple search
results = pipeline.search_meetings(
    query="decisions about API design",
    n_results=5,
)

# Tier-specific search
results = pipeline.search_meetings(
    query="compliance issues",
    tier=TierClassification.SENSITIVE,
    n_results=3,
)

# Cross-meeting question answering
results = pipeline.search_meetings(
    query="what did we decide about the Nordics launch?",
)
```

## Document Format

Each meeting is converted to a searchable document:

```
Meeting: {title}
Summary: {summary}

Decisions:
- {topic}: {decision}

Action Items:
- {owner}: {task}

Topics:
- {name} ({importance})
```

## Use Cases

1. **"What did we decide about X?"** — Find past decisions
2. **"Who is working on Y?"** — Identify owners
3. **"What were the concerns about Z?"** — Track issues over time
