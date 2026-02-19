# Changelog

All notable changes to Meeting Intelligence are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Sidebar and OpenAPI docs incorrectly showed "Claude Sonnet 4" instead of "Claude Haiku 4.5"

## [0.2.0] - 2026-02-19

### Added
- **Test suite** with 165 tests across three layers (unit, smoke, e2e)
  - 114 backend unit tests covering all 8 modules (93% coverage)
  - 27 smoke tests validating endpoint responses and schemas
  - 8 end-to-end tests with fakeredis for full pipeline flows
  - 16 frontend tests (Vitest) for API client and module exports
- Test infrastructure: `pytest-cov`, `fakeredis`, `httpx`, Vitest + happy-dom
- pytest markers for `smoke` and `e2e` test selection
- Frontend `npm test` and `npm run test:watch` scripts
- `CHANGELOG.md` following Keep a Changelog standard
- Updated test suite documentation in `docs/features/test-suite.md`

### Fixed
- TestClient lifespan safety: prevent app startup from overwriting mock pipelines
- TestClient resource cleanup: use context managers to avoid thread leaks
- Correct `mock_embedding` patch target for CI environments without cached models

## [0.1.0] - 2025-02-18

### Added
- **Two-tier privacy pipeline** with ordinary and sensitive classifications
  - Ordinary tier: direct LLM extraction
  - Sensitive tier: PII redaction (Presidio) before extraction, RBAC, full audit trail
- **Structured extraction** using Claude + Instructor + Pydantic 2
  - Decisions with confidence scores
  - Action items with owners, deadlines, priorities
  - Key topics with importance levels
  - Open questions with stakeholders
- **Per-speaker sentiment analysis** using BERT multilingual model
  - 1-5 star rating mapped to positive/neutral/negative
  - Key phrase extraction per speaker
  - Raw transcript parsing fallback
- **Semantic search** via sentence-transformers (all-MiniLM-L6-v2) + Redis
  - Cosine similarity computed in-process (no Redis Stack required)
  - Tiered namespaces (`ordinary:*` / `sensitive:*`)
  - Cross-meeting search support
- **PII redaction** with Microsoft Presidio
  - 8 entity types: person, phone, email, credit card, IBAN, location, datetime, NRP
  - Speaker name preservation option
  - Audit log generation per redaction
  - Regex-based fallback for environments without Presidio
- **FastAPI REST API** with 8 endpoints
  - `POST /api/v1/meetings/process` — process transcript
  - `GET /api/v1/meetings` — list meetings by tier
  - `GET /api/v1/meetings/{id}` — get meeting insights
  - `GET /api/v1/meetings/{id}/transcript` — get raw transcript
  - `GET /api/v1/meetings/search` — semantic search
  - `DELETE /api/v1/meetings/{id}` — delete meeting
  - `GET /api/v1/stats` — aggregate analytics
  - `POST /api/v1/admin/dedup` — remove duplicate meetings
- **Next.js 15 frontend** with shadcn/ui
  - Dashboard with meeting counts and quick stats
  - Process page for submitting transcripts
  - Meetings list with processing time display
  - Meeting detail page with full insights and transcript
  - Intelligence page with sentiment, topic, and priority analytics
  - Semantic search page
  - StormGeo branding with dark navy theme
  - Responsive sidebar with collapsible icon mode
  - Font size toggle, theme toggle (light/dark)
  - Sticky header with mobile optimizations
- **Railway deployment** with 3 services (backend, frontend, Redis)
- **Documentation**
  - Architecture overview with Mermaid and D2 diagrams
  - ADR-001: Two-tier privacy model decision record
  - Feature docs: privacy tiers, structured extraction, sentiment analysis, semantic search
  - Deployment guide for Railway
  - API endpoint reference
  - Batch processing roadmap
  - Test suite roadmap
- 20 realistic example transcripts for demo seeding

### Changed
- Migrated LLM from OpenAI to Anthropic Claude

### Fixed
- Docker build: removed stale `COPY public/` from backend Dockerfile
- API proxy: forward full pathname for Railway internal networking
- Search: correct field mapping for search results
- Dashboard: fetch both tiers to show correct total meeting count

### Performance
- Switched LLM from Claude Sonnet to Haiku for cost optimization

[unreleased]: https://github.com/anderson-ufrj/meeting-intelligence/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/anderson-ufrj/meeting-intelligence/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/anderson-ufrj/meeting-intelligence/releases/tag/v0.1.0
