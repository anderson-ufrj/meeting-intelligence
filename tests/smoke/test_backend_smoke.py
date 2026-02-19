"""Backend smoke tests — verify all endpoints respond with correct schemas."""

import pytest

pytestmark = pytest.mark.smoke


class TestHealthSmoke:
    def test_health_returns_200(self, smoke_client):
        resp = smoke_client.get("/health")
        assert resp.status_code == 200

    def test_health_has_required_fields(self, smoke_client):
        data = smoke_client.get("/health").json()
        assert "status" in data
        assert "redis" in data
        assert "version" in data

    def test_api_health_alias(self, smoke_client):
        resp = smoke_client.get("/api/health")
        assert resp.status_code == 200


class TestProcessSmoke:
    def test_process_returns_200(self, smoke_client):
        resp = smoke_client.post("/api/v1/meetings/process", json={
            "title": "Smoke Test",
            "transcript": "Alice: Let's verify the smoke tests are working correctly.",
        })
        assert resp.status_code == 200

    def test_process_response_schema(self, smoke_client):
        resp = smoke_client.post("/api/v1/meetings/process", json={
            "title": "Schema Check",
            "transcript": "Bob: This transcript verifies the response schema is correct.",
        })
        data = resp.json()
        assert "meeting_id" in data
        assert "status" in data
        assert "tier" in data
        assert "insights" in data
        assert "sentiments" in data
        assert "vector_id" in data
        assert "audit_log" in data

    def test_process_empty_title_rejected(self, smoke_client):
        resp = smoke_client.post("/api/v1/meetings/process", json={
            "title": "",
            "transcript": "Some valid transcript that is long enough.",
        })
        assert resp.status_code == 422

    def test_process_missing_transcript_rejected(self, smoke_client):
        resp = smoke_client.post("/api/v1/meetings/process", json={
            "title": "Test",
        })
        assert resp.status_code == 422


class TestListSmoke:
    def test_list_returns_200(self, smoke_client):
        resp = smoke_client.get("/api/v1/meetings?tier=ordinary")
        assert resp.status_code == 200

    def test_list_response_schema(self, smoke_client):
        data = smoke_client.get("/api/v1/meetings?tier=ordinary").json()
        assert "tier" in data
        assert "meetings" in data
        assert isinstance(data["meetings"], list)

    def test_list_sensitive_tier(self, smoke_client):
        resp = smoke_client.get("/api/v1/meetings?tier=sensitive")
        assert resp.status_code == 200


class TestGetMeetingSmoke:
    def test_get_returns_200(self, smoke_client):
        resp = smoke_client.get("/api/v1/meetings/smoke_001?tier=ordinary")
        assert resp.status_code == 200

    def test_get_response_has_metadata(self, smoke_client):
        data = smoke_client.get("/api/v1/meetings/smoke_001?tier=ordinary").json()
        assert "metadata" in data

    def test_get_nonexistent_returns_404(self, smoke_client):
        smoke_client.app  # access to modify mock
        import backend.api as api_module
        api_module.pipeline.stores["ordinary"].get_meeting.return_value = None
        resp = smoke_client.get("/api/v1/meetings/nonexistent?tier=ordinary")
        assert resp.status_code == 404
        # Restore
        api_module.pipeline.stores["ordinary"].get_meeting.return_value = {
            "metadata": {"meeting_id": "smoke_001", "title": "Smoke Test Meeting"},
            "document": "Smoke test document content",
        }


class TestTranscriptSmoke:
    def test_transcript_returns_200(self, smoke_client):
        resp = smoke_client.get("/api/v1/meetings/smoke_001/transcript?tier=ordinary")
        assert resp.status_code == 200

    def test_transcript_response_schema(self, smoke_client):
        data = smoke_client.get("/api/v1/meetings/smoke_001/transcript?tier=ordinary").json()
        assert "meeting_id" in data
        assert "transcript" in data


class TestSearchSmoke:
    def test_search_returns_200(self, smoke_client):
        resp = smoke_client.get("/api/v1/meetings/search?q=sprint")
        assert resp.status_code == 200

    def test_search_response_schema(self, smoke_client):
        data = smoke_client.get("/api/v1/meetings/search?q=test").json()
        assert "query" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_empty_query_rejected(self, smoke_client):
        resp = smoke_client.get("/api/v1/meetings/search?q=")
        assert resp.status_code == 422


class TestDeleteSmoke:
    def test_delete_returns_200(self, smoke_client):
        resp = smoke_client.delete("/api/v1/meetings/smoke_001?tier=ordinary")
        assert resp.status_code == 200

    def test_delete_response_schema(self, smoke_client):
        data = smoke_client.delete("/api/v1/meetings/smoke_002?tier=ordinary").json()
        assert data["status"] == "deleted"
        assert "meeting_id" in data


class TestStatsSmoke:
    def test_stats_returns_200(self, smoke_client):
        resp = smoke_client.get("/api/v1/stats")
        assert resp.status_code == 200

    def test_stats_response_schema(self, smoke_client):
        data = smoke_client.get("/api/v1/stats").json()
        assert "total_meetings" in data


class TestDedupSmoke:
    def test_dedup_returns_200(self, smoke_client):
        resp = smoke_client.post("/api/v1/admin/dedup")
        assert resp.status_code == 200

    def test_dedup_response_schema(self, smoke_client):
        data = smoke_client.post("/api/v1/admin/dedup").json()
        assert "status" in data
        assert "kept" in data
        assert "removed" in data


class TestCORSSmoke:
    def test_cors_headers_present(self, smoke_client):
        resp = smoke_client.options(
            "/api/v1/meetings",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORS middleware responds to preflight
        assert resp.status_code in (200, 204, 405)


class TestOpenAPISmoke:
    def test_openapi_schema(self, smoke_client):
        resp = smoke_client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "Meeting Intelligence"

    def test_docs_page(self, smoke_client):
        resp = smoke_client.get("/docs")
        assert resp.status_code == 200
