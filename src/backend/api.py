"""FastAPI application for Meeting Intelligence."""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from uuid import uuid4

import redis
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    description="Two-tier meeting intelligence pipeline for Microsoft Teams transcripts.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
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

    return {
        "meeting_id": result.meeting_id,
        "status": "processed",
        "tier": result.tier.value,
        "insights": result.insights.model_dump(),
        "sentiments": [s.model_dump() for s in result.sentiments],
        "vector_id": result.vector_id,
        "audit_log": result.audit_log,
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
