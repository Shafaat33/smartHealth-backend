import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import KNOWLEDGE_CHUNK_OVERLAP, KNOWLEDGE_CHUNK_SIZE, KNOWLEDGE_DIR
from app.repositories.knowledge import KnowledgeRepository
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    source: str
    page: int
    chunk_index: int
    content: str
    content_hash: str


@dataclass
class IngestionReport:
    files: int = 0
    chunks: int = 0
    embedded: int = 0
    unchanged: int = 0
    deleted: int = 0
    sources: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_pdf(path: Path, splitter: RecursiveCharacterTextSplitter) -> list[Chunk]:
    reader = PdfReader(str(path))
    chunks: list[Chunk] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = _normalize(page.extract_text() or "")
        if not text:
            continue
        for piece in splitter.split_text(text):
            chunks.append(
                Chunk(
                    source=path.name,
                    page=page_number,
                    chunk_index=len(chunks),
                    content=piece,
                    content_hash=hashlib.sha256(piece.encode("utf-8")).hexdigest(),
                )
            )
    return chunks


class IngestionService:
    def __init__(self, db: Session, embeddings: EmbeddingService | None = None):
        self.db = db
        self.knowledge = KnowledgeRepository(db)
        self._embeddings = embeddings
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=KNOWLEDGE_CHUNK_SIZE,
            chunk_overlap=KNOWLEDGE_CHUNK_OVERLAP,
        )

    @property
    def embeddings(self) -> EmbeddingService:
        if self._embeddings is None:
            self._embeddings = EmbeddingService()
        return self._embeddings

    def ingest_directory(self, directory: str | Path = KNOWLEDGE_DIR) -> IngestionReport:
        directory = Path(directory)
        if not directory.is_dir():
            raise FileNotFoundError(f"Knowledge directory not found: {directory}")

        report = IngestionReport()
        paths = sorted(directory.glob("*.pdf"))
        try:
            for path in paths:
                self._ingest_file(path, report)
            report.deleted += self.knowledge.delete_sources_except([p.name for p in paths])
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        logger.info(
            "knowledge ingestion: files=%d chunks=%d embedded=%d unchanged=%d deleted=%d",
            report.files,
            report.chunks,
            report.embedded,
            report.unchanged,
            report.deleted,
        )
        return report

    def _ingest_file(self, path: Path, report: IngestionReport) -> None:
        chunks = chunk_pdf(path, self.splitter)
        existing = self.knowledge.hashes_for_source(path.name)
        changed = [c for c in chunks if existing.get(c.chunk_index) != c.content_hash]

        if changed:
            vectors = self.embeddings.embed([c.content for c in changed])
            self.knowledge.upsert(
                [
                    {
                        "source": c.source,
                        "page": c.page,
                        "chunk_index": c.chunk_index,
                        "content": c.content,
                        "content_hash": c.content_hash,
                        "embedding": vector,
                    }
                    for c, vector in zip(changed, vectors, strict=True)
                ]
            )

        report.files += 1
        report.chunks += len(chunks)
        report.embedded += len(changed)
        report.unchanged += len(chunks) - len(changed)
        report.deleted += self.knowledge.delete_from_index(path.name, len(chunks))
        report.sources.append(path.name)
