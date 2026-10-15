from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk


class KnowledgeRepository:
    def __init__(self, db: Session):
        self.db = db

    def hashes_for_source(self, source: str) -> dict[int, str]:
        rows = self.db.execute(
            select(KnowledgeChunk.chunk_index, KnowledgeChunk.content_hash).where(
                KnowledgeChunk.source == source
            )
        ).all()
        return {chunk_index: content_hash for chunk_index, content_hash in rows}

    def upsert(self, rows: list[dict]) -> None:
        if not rows:
            return
        stmt = insert(KnowledgeChunk).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_knowledge_chunk_source_index",
            set_={
                "page": stmt.excluded.page,
                "content": stmt.excluded.content,
                "content_hash": stmt.excluded.content_hash,
                "embedding": stmt.excluded.embedding,
            },
        )
        self.db.execute(stmt)

    def delete_from_index(self, source: str, first_stale_index: int) -> int:
        result = self.db.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.source == source,
                KnowledgeChunk.chunk_index >= first_stale_index,
            )
        )
        return result.rowcount

    def nearest(
        self,
        vector: list[float],
        k: int,
        max_distance: float,
    ) -> list[tuple[KnowledgeChunk, float]]:
        distance = KnowledgeChunk.embedding.cosine_distance(vector).label("distance")
        rows = self.db.execute(
            select(KnowledgeChunk, distance).order_by(distance).limit(k)
        ).all()
        return [(chunk, dist) for chunk, dist in rows if dist <= max_distance]

    def delete_sources_except(self, keep: list[str]) -> int:
        result = self.db.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.source.not_in(keep))
        )
        return result.rowcount