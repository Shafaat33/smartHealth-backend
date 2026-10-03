from openai import OpenAI

from app.core.config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
)


class EmbeddingService:
    def __init__(self, client: OpenAI | None = None):
        if client is None:
            if not OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY is not set")
            client = OpenAI(api_key=OPENAI_API_KEY, max_retries=3, timeout=30)
        self.client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[start : start + EMBEDDING_BATCH_SIZE]
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
                dimensions=EMBEDDING_DIM,
            )
            vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
        return vectors
