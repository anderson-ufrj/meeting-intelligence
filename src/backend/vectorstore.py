"""Vector store and semantic search using Redis + sentence-transformers."""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

import numpy as np
import redis

from .models import ProcessedMeeting


@dataclass
class SearchResult:
    """Result from semantic search."""
    meeting_id: str
    score: float
    content: str
    metadata: Dict


class MeetingVectorStore:
    """Store and search meeting embeddings using Redis.

    Uses sentence-transformers (local, no API key needed) for embeddings
    and Redis for persistence. Semantic search via cosine similarity
    computed in-process — works with any Redis version (no Stack required).
    """

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(
        self,
        redis_url: Optional[str] = None,
        namespace: str = "default",
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.namespace = namespace
        self.r = redis.from_url(self.redis_url, decode_responses=True)
        self._model = None

    @property
    def embedding_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.EMBEDDING_MODEL)
        return self._model

    # ── Keys ──────────────────────────────────────────────────────────

    def _data_key(self, meeting_id: str) -> str:
        return f"meeting:{self.namespace}:{meeting_id}"

    def _emb_key(self, meeting_id: str) -> str:
        return f"emb:{self.namespace}:{meeting_id}"

    def _index_key(self) -> str:
        return f"idx:{self.namespace}"

    # ── Embeddings ────────────────────────────────────────────────────

    def _get_embedding(self, text: str) -> List[float]:
        embedding = self.embedding_model.encode(text[:8000], normalize_embeddings=True)
        return embedding.tolist()

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        va = np.asarray(a, dtype=np.float32)
        vb = np.asarray(b, dtype=np.float32)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    # ── CRUD ──────────────────────────────────────────────────────────

    def add_meeting(
        self,
        meeting: ProcessedMeeting,
        namespace: Optional[str] = None,
    ) -> str:
        ns = namespace or self.namespace
        vector_id = f"{ns}_{meeting.meeting_id}"

        document = self._meeting_to_document(meeting)
        metadata = {
            "meeting_id": meeting.meeting_id,
            "tier": meeting.tier.value,
            "namespace": ns,
            "processed_at": meeting.processed_at.isoformat(),
            "title": meeting.insights.meeting_title,
        }

        payload = {
            "document": document,
            "metadata": metadata,
            "vector_id": vector_id,
            "processed_meeting": meeting.model_dump(mode="json"),
        }

        pipe = self.r.pipeline()
        pipe.set(self._data_key(meeting.meeting_id), json.dumps(payload))
        pipe.sadd(self._index_key(), meeting.meeting_id)
        pipe.execute()

        embedding = self._get_embedding(document)
        self.r.set(self._emb_key(meeting.meeting_id), json.dumps(embedding))

        return vector_id

    def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        raw = self.r.get(self._data_key(meeting_id))
        if not raw:
            return None
        return json.loads(raw)

    def list_meetings(self) -> List[Dict]:
        meeting_ids = self.r.smembers(self._index_key())
        meetings = []
        for mid in sorted(meeting_ids):
            data = self.get_meeting(mid)
            if data:
                meetings.append(data["metadata"])
        return meetings

    def delete_meeting(self, meeting_id: str, namespace: Optional[str] = None) -> None:
        pipe = self.r.pipeline()
        pipe.delete(self._data_key(meeting_id))
        pipe.delete(self._emb_key(meeting_id))
        pipe.srem(self._index_key(), meeting_id)
        pipe.execute()

    # ── Search ────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        namespace: Optional[str] = None,
        n_results: int = 5,
        filter_dict: Optional[Dict] = None,
    ) -> List[SearchResult]:
        ns = namespace or self.namespace
        meeting_ids = self.r.smembers(f"idx:{ns}")
        if not meeting_ids:
            return []

        query_embedding = self._get_embedding(query)

        results: List[SearchResult] = []
        for mid in meeting_ids:
            emb_raw = self.r.get(f"emb:{ns}:{mid}")
            data_raw = self.r.get(f"meeting:{ns}:{mid}")
            if not emb_raw or not data_raw:
                continue

            meeting_embedding = json.loads(emb_raw)
            score = self._cosine_similarity(query_embedding, meeting_embedding)
            data = json.loads(data_raw)

            results.append(SearchResult(
                meeting_id=data["metadata"].get("meeting_id", mid),
                score=score,
                content=data["document"],
                metadata=data["metadata"],
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:n_results]

    def cross_meeting_search(
        self,
        topic: str,
        namespaces: Optional[List[str]] = None,
    ) -> Dict[str, List[SearchResult]]:
        namespaces = namespaces or [self.namespace]
        return {ns: self.search(topic, namespace=ns) for ns in namespaces}

    # ── Helpers ───────────────────────────────────────────────────────

    def _meeting_to_document(self, meeting: ProcessedMeeting) -> str:
        insights = meeting.insights

        sections = [
            f"Meeting: {insights.meeting_title}",
            f"Summary: {insights.summary}",
            "\nDecisions:",
        ]

        for d in insights.decisions:
            sections.append(f"- {d.topic}: {d.decision}")

        sections.append("\nAction Items:")
        for a in insights.action_items:
            deadline = f" (by {a.deadline})" if a.deadline else ""
            sections.append(f"- {a.owner}: {a.task}{deadline}")

        sections.append("\nTopics:")
        for t in insights.key_topics:
            sections.append(f"- {t.name} ({t.importance})")

        if insights.open_questions:
            sections.append("\nOpen Questions:")
            for q in insights.open_questions:
                sections.append(f"- {q.question}")

        return "\n".join(sections)


def create_tiered_stores(
    redis_url: Optional[str] = None,
) -> Dict[str, MeetingVectorStore]:
    """Create separate vector stores for ordinary and sensitive tiers."""
    url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
    return {
        "ordinary": MeetingVectorStore(redis_url=url, namespace="ordinary"),
        "sensitive": MeetingVectorStore(redis_url=url, namespace="sensitive"),
    }
