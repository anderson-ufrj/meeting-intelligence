# Batch Processing — Roadmap

## Problem

Currently, meetings are processed one at a time via `POST /api/v1/meetings/process`. When onboarding a new team or importing historical transcripts, users must submit each meeting individually. This is slow, error-prone, and blocks the UI during long-running extractions.

For StormGeo's use case — teams generating dozens of meeting transcripts weekly across shipping, energy, and weather operations — batch ingestion is essential for production adoption.

## Proposed Solution

A batch processing endpoint that accepts multiple transcripts in a single request, processes them asynchronously, and provides real-time progress tracking.

## API Design

### Submit Batch

```http
POST /api/v1/meetings/batch
Content-Type: application/json

{
  "meetings": [
    { "title": "Sprint Planning", "tier": "ordinary", "transcript": "..." },
    { "title": "Security Audit", "tier": "sensitive", "transcript": "..." }
  ]
}
```

**Response** (immediate):

```json
{
  "batch_id": "batch_a1b2c3d4",
  "total": 2,
  "status": "processing",
  "submitted_at": "2025-02-18T18:00:00Z"
}
```

### Check Progress

```http
GET /api/v1/meetings/batch/{batch_id}
```

**Response:**

```json
{
  "batch_id": "batch_a1b2c3d4",
  "total": 2,
  "completed": 1,
  "failed": 0,
  "status": "processing",
  "results": [
    { "meeting_id": "meeting_abc123", "title": "Sprint Planning", "status": "completed" },
    { "meeting_id": null, "title": "Security Audit", "status": "processing" }
  ]
}
```

## Architecture

```
Client                    API                     Pipeline
  |                        |                         |
  |--- POST /batch ------->|                         |
  |<-- 202 batch_id -------|                         |
  |                        |-- enqueue meeting 1 --->|
  |                        |-- enqueue meeting 2 --->|
  |                        |          ...            |
  |--- GET /batch/id ----->|                         |
  |<-- progress ---------- |                         |
  |                        |<-- result 1 ----------- |
  |--- GET /batch/id ----->|                         |
  |<-- progress (1/2) -----|                         |
  |                        |<-- result 2 ----------- |
  |--- GET /batch/id ----->|                         |
  |<-- complete (2/2) -----|                         |
```

## Implementation Phases

### Phase 1 — Sequential Batch (MVP)

Process meetings sequentially in a background thread. Simple, no new infrastructure.

- `POST /api/v1/meetings/batch` accepts up to 50 meetings
- Spawns a `threading.Thread` that calls `pipeline.process()` in a loop
- Batch state stored in Redis (`batch:{batch_id}` key)
- `GET /api/v1/meetings/batch/{batch_id}` polls progress
- Frontend shows a progress bar with per-meeting status

**Effort**: ~2 days
**Limitation**: Sequential processing (~30-60s per meeting)

### Phase 2 — Concurrent Processing

Use a thread pool to process multiple meetings in parallel.

- `concurrent.futures.ThreadPoolExecutor` with configurable `max_workers`
- Default 3 workers (balanced against API rate limits and memory)
- Per-meeting error isolation — one failure doesn't block others
- Retry logic for transient LLM API failures (max 2 retries)

**Effort**: ~1 day on top of Phase 1
**Improvement**: 3x throughput (10-20s effective per meeting)

### Phase 3 — File Upload Support

Accept `.vtt`, `.txt`, and `.zip` file uploads instead of JSON body.

- `POST /api/v1/meetings/batch/upload` with `multipart/form-data`
- Auto-detect transcript format (Teams VTT, plain text, SRT)
- ZIP files extracted and each file treated as a separate meeting
- Title inferred from filename if not provided

**Effort**: ~2 days
**Dependency**: Phase 1

### Phase 4 — Frontend Batch UI

Dedicated batch upload page in the Next.js frontend.

- Drag-and-drop zone for multiple files
- Table showing upload queue with per-file status
- Real-time progress via polling (`GET /batch/{id}` every 2s)
- Error details expandable per meeting
- "Process All" button with tier selection (ordinary/sensitive)

**Effort**: ~3 days
**Dependency**: Phase 1 + Phase 3

## Deduplication

Batch processing must handle duplicates gracefully:

- Before processing, check if a meeting with the same title + tier already exists
- Options: `skip` (default), `replace`, or `allow_duplicates`
- Controlled via request parameter: `"on_duplicate": "skip"`

```json
{
  "meetings": [...],
  "on_duplicate": "skip"
}
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Single meeting fails LLM extraction | Mark as `failed`, continue batch |
| LLM API rate limited | Exponential backoff, retry up to 2x |
| Redis connection lost | Fail entire batch with `partial` status |
| Invalid transcript (too short) | Reject at validation, mark as `skipped` |
| Batch exceeds 50 meetings | Return 400 with limit message |

## Redis Storage Schema

```
batch:{batch_id}          → JSON { total, completed, failed, status, submitted_at }
batch:{batch_id}:results  → JSON [ { meeting_id, title, status, error? } ]
```

TTL: 24 hours after batch completion (auto-cleanup).

## Success Metrics

- Process 20 meetings in under 5 minutes (Phase 2)
- Zero data loss on partial failures
- Frontend shows real-time progress within 2s latency

## Priority

**Medium** — The current single-meeting endpoint works for demos and small teams. Batch becomes critical when scaling to real-world Teams transcript volumes (10-50 meetings/week per team).
