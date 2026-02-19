"""Tests for Redis vector store module (Phase 3)."""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.models import ProcessedMeeting, TierClassification
from backend.vectorstore import MeetingVectorStore, SearchResult, create_tiered_stores


@pytest.fixture
def mock_redis_store():
    """Create a MeetingVectorStore with mocked Redis and SentenceTransformer."""
    with patch("backend.vectorstore.redis.from_url") as mock_redis_factory:
        mock_redis_instance = MagicMock()
        mock_redis_factory.return_value = mock_redis_instance

        store = MeetingVectorStore(redis_url="redis://fake:6379", namespace="ordinary")
        # Mock the embedding model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        store._model = mock_model

        yield store, mock_redis_instance


class TestKeyGeneration:
    def test_data_key(self, mock_redis_store):
        store, _ = mock_redis_store
        assert store._data_key("m1") == "meeting:ordinary:m1"

    def test_emb_key(self, mock_redis_store):
        store, _ = mock_redis_store
        assert store._emb_key("m1") == "emb:ordinary:m1"

    def test_index_key(self, mock_redis_store):
        store, _ = mock_redis_store
        assert store._index_key() == "idx:ordinary"

    def test_different_namespace(self):
        with patch("backend.vectorstore.redis.from_url"):
            store = MeetingVectorStore(redis_url="redis://fake:6379", namespace="sensitive")
            assert store._data_key("m1") == "meeting:sensitive:m1"
            assert store._index_key() == "idx:sensitive"


class TestAddMeeting:
    def test_stores_data_and_embedding(self, mock_redis_store, sample_processed_meeting):
        store, mock_redis = mock_redis_store

        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline

        vector_id = store.add_meeting(sample_processed_meeting)

        assert vector_id == "ordinary_test_meeting_001"
        mock_pipeline.set.assert_called_once()
        mock_pipeline.sadd.assert_called_once()
        mock_pipeline.execute.assert_called_once()
        mock_redis.set.assert_called_once()  # embedding


class TestGetMeeting:
    def test_found(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        payload = {"metadata": {"meeting_id": "m1"}, "document": "test"}
        mock_redis.get.return_value = json.dumps(payload)

        result = store.get_meeting("m1")
        assert result is not None
        assert result["metadata"]["meeting_id"] == "m1"

    def test_not_found(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        mock_redis.get.return_value = None

        result = store.get_meeting("nonexistent")
        assert result is None


class TestListMeetings:
    def test_returns_sorted_metadata(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        mock_redis.smembers.return_value = {"m2", "m1"}

        payload1 = {"metadata": {"meeting_id": "m1", "title": "First"}, "document": "doc1"}
        payload2 = {"metadata": {"meeting_id": "m2", "title": "Second"}, "document": "doc2"}

        def get_side_effect(key):
            if "m1" in key:
                return json.dumps(payload1)
            if "m2" in key:
                return json.dumps(payload2)
            return None

        mock_redis.get.side_effect = get_side_effect

        result = store.list_meetings()
        assert len(result) == 2
        assert result[0]["meeting_id"] == "m1"
        assert result[1]["meeting_id"] == "m2"

    def test_empty_namespace(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        mock_redis.smembers.return_value = set()

        result = store.list_meetings()
        assert result == []


class TestDeleteMeeting:
    def test_removes_all_keys(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline

        store.delete_meeting("m1")

        mock_pipeline.delete.assert_any_call("meeting:ordinary:m1")
        mock_pipeline.delete.assert_any_call("emb:ordinary:m1")
        mock_pipeline.srem.assert_called_once_with("idx:ordinary", "m1")
        mock_pipeline.execute.assert_called_once()


class TestSearch:
    def test_returns_ranked_results(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        mock_redis.smembers.return_value = {"m1", "m2"}

        emb1 = np.random.rand(384).tolist()
        emb2 = np.random.rand(384).tolist()
        data1 = json.dumps({
            "metadata": {"meeting_id": "m1", "title": "First"},
            "document": "Sprint review discussion",
        })
        data2 = json.dumps({
            "metadata": {"meeting_id": "m2", "title": "Second"},
            "document": "Budget planning session",
        })

        def get_side_effect(key):
            if key == "emb:ordinary:m1":
                return json.dumps(emb1)
            if key == "emb:ordinary:m2":
                return json.dumps(emb2)
            if key == "meeting:ordinary:m1":
                return data1
            if key == "meeting:ordinary:m2":
                return data2
            return None

        mock_redis.get.side_effect = get_side_effect

        results = store.search("sprint review")
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        # Results sorted by score descending
        assert results[0].score >= results[1].score

    def test_empty_namespace(self, mock_redis_store):
        store, mock_redis = mock_redis_store
        mock_redis.smembers.return_value = set()

        results = store.search("anything")
        assert results == []


class TestCosineSimilarity:
    def test_identical_vectors(self):
        vec = [1.0, 0.0, 0.0]
        score = MeetingVectorStore._cosine_similarity(vec, vec)
        assert abs(score - 1.0) < 0.01

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        score = MeetingVectorStore._cosine_similarity(a, b)
        assert abs(score) < 0.01

    def test_zero_norm_returns_zero(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        score = MeetingVectorStore._cosine_similarity(a, b)
        assert score == 0.0


class TestCreateTieredStores:
    def test_returns_both_tiers(self):
        with patch("backend.vectorstore.redis.from_url"):
            stores = create_tiered_stores(redis_url="redis://fake:6379")
            assert "ordinary" in stores
            assert "sensitive" in stores
            assert isinstance(stores["ordinary"], MeetingVectorStore)
            assert isinstance(stores["sensitive"], MeetingVectorStore)

    def test_namespaces_match_tiers(self):
        with patch("backend.vectorstore.redis.from_url"):
            stores = create_tiered_stores(redis_url="redis://fake:6379")
            assert stores["ordinary"].namespace == "ordinary"
            assert stores["sensitive"].namespace == "sensitive"
