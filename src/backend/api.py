"""FastAPI application for Meeting Intelligence."""

import json
import os
import logging
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from uuid import uuid4

import redis
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .parsers import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, parse_file

from . import __version__
from .models import (
    MeetingTranscript,
    TierClassification,
)
from .pipeline import MeetingPipeline

logger = logging.getLogger(__name__)

# ── Request / Response schemas ────────────────────────────────────────

class ProcessRequest(BaseModel):
    meeting_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    date: Optional[datetime] = None
    tier: str = Field("ordinary", pattern="^(ordinary|sensitive)$")
    transcript: str = Field(..., min_length=10)


class HealthResponse(BaseModel):
    status: str
    redis: str
    version: str


# ── App lifecycle ─────────────────────────────────────────────────────

pipeline: Optional[MeetingPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("Initializing pipeline...")
    pipeline = MeetingPipeline(
        redis_url=os.getenv("REDIS_URL"),
    )
    logger.info("Pipeline ready.")
    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Meeting Intelligence",
    description=(
        "Two-tier meeting intelligence pipeline for Microsoft Teams transcripts.\n\n"
        "**Proof of Concept** built by **Anderson Henrique da Silva** for StormGeo.\n\n"
        "## Pipeline\n\n"
        "1. **Structured Extraction** — Claude Haiku 4.5 via Instructor for decisions, "
        "action items, topics, and open questions\n"
        "2. **Sentiment Analysis** — BERT-based per-speaker sentiment scoring\n"
        "3. **PII Redaction** — Presidio-powered anonymization for sensitive tiers\n"
        "4. **Semantic Indexing** — Sentence-transformers (all-MiniLM-L6-v2) embeddings "
        "stored in Redis for cosine-similarity search\n\n"
        "## Stack\n\n"
        "FastAPI, Anthropic Claude, Sentence Transformers, Redis, Presidio, Pydantic 2"
    ),
    version=__version__,
    lifespan=lifespan,
    contact={
        "name": "Anderson Henrique da Silva",
        "url": "https://github.com/anderson-ufrj",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse, include_in_schema=False)
def health():
    redis_status = "disconnected"
    try:
        r = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True,
        )
        r.ping()
        redis_status = "connected"
    except Exception:
        pass
    return HealthResponse(
        status="healthy" if redis_status == "connected" else "degraded",
        redis=redis_status,
        version=__version__,
    )


@app.post("/api/v1/meetings/process")
def process_meeting(req: ProcessRequest):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    meeting_id = req.meeting_id or f"meeting_{uuid4().hex[:12]}"
    tier = TierClassification(req.tier)

    transcript = MeetingTranscript(
        meeting_id=meeting_id,
        title=req.title,
        date=req.date or datetime.utcnow(),
        tier=tier,
        raw_text=req.transcript,
    )

    try:
        result = pipeline.process(transcript)
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(500, f"Processing failed: {e}")

    # Persist the original transcript alongside the processed meeting
    store = pipeline.stores.get(tier.value)
    if store:
        transcript_key = f"transcript:{store.namespace}:{result.meeting_id}"
        store.r.set(transcript_key, req.transcript)

    return {
        "meeting_id": result.meeting_id,
        "status": "processed",
        "tier": result.tier.value,
        "insights": result.insights.model_dump(),
        "sentiments": [s.model_dump() for s in result.sentiments],
        "vector_id": result.vector_id,
        "audit_log": result.audit_log,
    }


@app.post("/api/v1/meetings/upload")
async def upload_meeting(
    file: UploadFile = File(...),
    title: str = Form(""),
    tier: str = Form("ordinary"),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    if tier not in ("ordinary", "sensitive"):
        raise HTTPException(422, f"Invalid tier: {tier}")

    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            422,
            f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(422, "File is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit")

    try:
        result = parse_file(content, file.filename or "file" + ext)
    except Exception as e:
        logger.exception("File parsing failed")
        raise HTTPException(422, f"Failed to parse file: {e}")

    effective_title = title.strip() or result.detected_title or file.filename or "Untitled"
    meeting_id = f"meeting_{uuid4().hex[:12]}"
    tier_enum = TierClassification(tier)

    transcript = MeetingTranscript(
        meeting_id=meeting_id,
        title=effective_title,
        date=datetime.utcnow(),
        tier=tier_enum,
        raw_text=result.text,
    )

    try:
        processed = pipeline.process(transcript)
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(500, f"Processing failed: {e}")

    store = pipeline.stores.get(tier)
    if store:
        transcript_key = f"transcript:{store.namespace}:{processed.meeting_id}"
        store.r.set(transcript_key, result.text)

    return {
        "meeting_id": processed.meeting_id,
        "status": "processed",
        "tier": processed.tier.value,
        "source_format": result.format,
        "insights": processed.insights.model_dump(),
        "sentiments": [s.model_dump() for s in processed.sentiments],
        "vector_id": processed.vector_id,
        "audit_log": processed.audit_log,
    }


@app.get("/api/v1/meetings/search")
def search_meetings(
    q: str = Query(..., min_length=1),
    tier: Optional[str] = Query(None, pattern="^(ordinary|sensitive)$"),
    limit: int = Query(10, ge=1, le=50),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    tier_enum = TierClassification(tier) if tier else None

    try:
        results = pipeline.search_meetings(q, tier=tier_enum, n_results=limit)
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(500, f"Search failed: {e}")

    return {"query": q, "results": results}


@app.get("/api/v1/meetings")
def list_meetings(
    tier: str = Query("ordinary", pattern="^(ordinary|sensitive)$"),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    store = pipeline.stores.get(tier)
    if not store:
        raise HTTPException(400, f"Unknown tier: {tier}")

    return {"tier": tier, "meetings": store.list_meetings()}


@app.get("/api/v1/meetings/{meeting_id}")
def get_meeting(
    meeting_id: str,
    tier: str = Query("ordinary", pattern="^(ordinary|sensitive)$"),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    store = pipeline.stores.get(tier)
    if not store:
        raise HTTPException(400, f"Unknown tier: {tier}")

    data = store.get_meeting(meeting_id)
    if not data:
        raise HTTPException(404, "Meeting not found")

    return data


@app.get("/api/v1/meetings/{meeting_id}/transcript")
def get_transcript(
    meeting_id: str,
    tier: str = Query("ordinary", pattern="^(ordinary|sensitive)$"),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    store = pipeline.stores.get(tier)
    if not store:
        raise HTTPException(400, f"Unknown tier: {tier}")

    transcript_key = f"transcript:{store.namespace}:{meeting_id}"
    raw = store.r.get(transcript_key)
    if not raw:
        raise HTTPException(404, "Transcript not found")

    return {"meeting_id": meeting_id, "transcript": raw}


@app.get("/api/v1/stats")
def get_stats():
    """Aggregate intelligence across all meetings."""
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    all_meetings = []
    for tier_name, store in pipeline.stores.items():
        meeting_ids = store.r.smembers(store._index_key())
        for mid in meeting_ids:
            raw = store.r.get(store._data_key(mid))
            if raw:
                all_meetings.append(json.loads(raw))

    total = len(all_meetings)
    if total == 0:
        return {"total_meetings": 0}

    sentiment_counts: Counter = Counter()
    speaker_sentiments: dict = {}
    topic_counts: Counter = Counter()
    priority_counts: Counter = Counter()
    total_decisions = 0
    total_actions = 0
    total_questions = 0
    speakers_set: set = set()
    tier_counts: Counter = Counter()

    for m in all_meetings:
        pm = m.get("processed_meeting", {})
        insights = pm.get("insights", {})
        sentiments = pm.get("sentiments", [])
        tier_counts[pm.get("tier", "ordinary")] += 1

        decisions = insights.get("decisions", [])
        actions = insights.get("action_items", [])
        topics = insights.get("key_topics", [])
        questions = insights.get("open_questions", [])

        total_decisions += len(decisions)
        total_actions += len(actions)
        total_questions += len(questions)

        for t in topics:
            topic_counts[t.get("name", "")] += 1

        for a in actions:
            p = a.get("priority", "medium")
            if p:
                priority_counts[p.lower()] += 1
            owner = a.get("owner", "")
            if owner:
                speakers_set.add(owner)

        for s in sentiments:
            label = s.get("overall_sentiment", "neutral")
            sentiment_counts[label] += 1
            speaker = s.get("speaker", "Unknown")
            speakers_set.add(speaker)
            if speaker not in speaker_sentiments:
                speaker_sentiments[speaker] = {"positive": 0, "neutral": 0, "negative": 0}
            speaker_sentiments[speaker][label] = (
                speaker_sentiments[speaker].get(label, 0) + 1
            )

    return {
        "total_meetings": total,
        "total_decisions": total_decisions,
        "total_actions": total_actions,
        "total_questions": total_questions,
        "total_speakers": len(speakers_set),
        "tier_breakdown": dict(tier_counts),
        "sentiment_distribution": dict(sentiment_counts),
        "top_topics": topic_counts.most_common(20),
        "priority_breakdown": dict(priority_counts),
        "speaker_sentiments": dict(
            sorted(speaker_sentiments.items(), key=lambda x: sum(x[1].values()), reverse=True)[:15]
        ),
    }


@app.delete("/api/v1/meetings/{meeting_id}")
def delete_meeting(
    meeting_id: str,
    tier: str = Query("ordinary", pattern="^(ordinary|sensitive)$"),
):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    store = pipeline.stores.get(tier)
    if not store:
        raise HTTPException(400, f"Unknown tier: {tier}")

    store.delete_meeting(meeting_id)
    return {"status": "deleted", "meeting_id": meeting_id}


@app.post("/api/v1/admin/dedup")
def deduplicate_meetings():
    """Remove duplicate meetings, keeping only the most recent per title+tier."""
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")

    removed = 0
    kept = 0

    for tier_name, store in pipeline.stores.items():
        meeting_ids = store.r.smembers(store._index_key())
        meetings_by_title: dict[str, list[dict]] = {}

        for mid in meeting_ids:
            raw = store.r.get(store._data_key(mid))
            if not raw:
                continue
            data = json.loads(raw)
            title = data.get("metadata", {}).get("title", "")
            processed_at = data.get("metadata", {}).get("processed_at", "")
            meetings_by_title.setdefault(title, []).append({
                "meeting_id": mid,
                "processed_at": processed_at,
            })

        for title, entries in meetings_by_title.items():
            entries.sort(key=lambda e: e["processed_at"], reverse=True)
            kept += 1
            for dup in entries[1:]:
                store.delete_meeting(dup["meeting_id"])
                transcript_key = f"transcript:{store.namespace}:{dup['meeting_id']}"
                store.r.delete(transcript_key)
                removed += 1

    return {"status": "deduplicated", "kept": kept, "removed": removed}
