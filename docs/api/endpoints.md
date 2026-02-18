# API Endpoints

## FastAPI Application

REST API for the Meeting Intelligence system. Deployed on Railway.

## Base URL

```
https://<service>.up.railway.app/api/v1
```

## Endpoints

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "version": "0.1.0"
}
```

### Process Meeting

```http
POST /api/v1/meetings/process
Content-Type: application/json

{
  "meeting_id": "string",
  "title": "string",
  "date": "2025-01-15T10:00:00Z",
  "tier": "ordinary | sensitive",
  "transcript": "string"
}
```

Response:
```json
{
  "meeting_id": "string",
  "status": "processed",
  "tier": "ordinary",
  "insights": {
    "summary": "string",
    "decisions": [...],
    "action_items": [...],
    "key_topics": [...],
    "open_questions": [...]
  },
  "sentiments": [...],
  "vector_id": "string"
}
```

### Search Meetings

```http
GET /api/v1/meetings/search?q={query}&tier={tier}&limit=10
```

Response:
```json
{
  "query": "string",
  "results": [
    {
      "meeting_id": "string",
      "title": "string",
      "score": 0.89,
      "tier": "ordinary",
      "content_preview": "string"
    }
  ]
}
```

### List Meetings

```http
GET /api/v1/meetings?tier={tier}
```

### Get Meeting

```http
GET /api/v1/meetings/{meeting_id}?tier={tier}
```

### Delete Meeting

```http
DELETE /api/v1/meetings/{meeting_id}?tier={tier}
```

## Interactive Docs

Swagger UI available at `/docs` and ReDoc at `/redoc`.

## Error Responses

```json
{
  "detail": "Meeting not found"
}
```

Standard HTTP status codes: 200, 201, 400, 404, 500.
