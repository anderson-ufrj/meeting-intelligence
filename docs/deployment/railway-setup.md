# Railway Deployment Guide

## Overview

The application deploys as three services on Railway:

| Service | Type | Port |
|---------|------|------|
| **Backend** | FastAPI (Docker) | 8000 |
| **Frontend** | Next.js (Docker) | 3000 |
| **Redis** | Railway plugin | 6379 |

## Services Setup

### 1. Redis (Native Plugin)

Add Redis directly from Railway's service menu. The `REDIS_URL` variable is injected automatically into linked services.

### 2. Backend (FastAPI)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .
RUN python -m spacy download en_core_web_lg
EXPOSE 8000
CMD ["uvicorn", "meeting_intelligence.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Frontend (Next.js)

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next .next
COPY --from=builder /app/public public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules node_modules
EXPOSE 3000
CMD ["npm", "start"]
```

## Environment Variables

### Backend

```bash
OPENAI_API_KEY=sk-...          # Required: LLM extraction + embeddings
REDIS_URL=${{Redis.REDIS_URL}} # Auto-injected by Railway
LOG_LEVEL=INFO
CORS_ORIGINS=https://<frontend-domain>.up.railway.app
```

### Frontend

```bash
NEXT_PUBLIC_API_URL=https://<backend-domain>.up.railway.app
```

## Railway Configuration

Each service has a `railway.toml` or is configured via the dashboard:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

## Security Considerations

1. **CORS**: Restrict to frontend domain only
2. **Secrets**: Use Railway's encrypted variables
3. **Redis**: Internal network only (not exposed publicly)
4. **HTTPS**: Automatic via Railway's edge proxy

## Scaling

Railway auto-scales based on traffic. For production:

- Backend: 512MB+ RAM (BERT model loaded in memory)
- Redis: 256MB+ (embeddings storage)
- Frontend: Minimal (static + SSR)
