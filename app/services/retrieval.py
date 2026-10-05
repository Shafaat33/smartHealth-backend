import logging
from dataclasses import dataclass

from app.core.config import RETRIEVAL_MAX_DISTANCE, RETRIEVAL_TOP_K
from app.db.base import SessionLocal
from app.repositories.knowledge import KnowledgeRepository
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    page: int
    content: str
    distance: float


class RetrievalService:
    def __init__(self, embeddings: EmbeddingService | None = None):
        self.embeddings = embeddings or EmbeddingService()

    def search(
        self,
        question: str,
        k: int = RETRIEVAL_TOP_K,
        max_distance: float = RETRIEVAL_MAX_DISTANCE,
    ) -> list[RetrievedChunk]:
        vector = self.embeddings.embed([question])[0]
        # Own short-lived session: callers may be mid-stream long after the request session is gone.
        with SessionLocal() as db:
            hits = KnowledgeRepository(db).nearest(vector, k, max_distance)
            chunks = [
                RetrievedChunk(
                    source=chunk.source,
                    page=chunk.page,
                    content=chunk.content,
                    distance=float(distance),
                )
                for chunk, distance in hits
            ]
        logger.info(
            "retrieval k=%d max_distance=%.2f hits=%s",
            k,
            max_distance,
            [(c.source, c.page, round(c.distance, 3)) for c in chunks],
        )
        return chunks
