"""Local text embeddings for retrieval and Qdrant indexing."""

import asyncio
import logging
import time
from typing import List

from sentence_transformers import SentenceTransformer

from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    """Generate free local embeddings without an external provider API."""

    def __init__(self) -> None:
        self.model_name = settings.LOCAL_EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        if not self.dimension:
            raise ValueError(f"Could not determine embedding dimension for {self.model_name}")
        logger.info(
            "EmbeddingService initialized with model %s (dimension: %s)",
            self.model_name,
            self.dimension,
        )

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not isinstance(texts, list):
            raise ValueError(f"Expected list of texts, got {type(texts)}")
        if not texts:
            return []
        if any(not text or not text.strip() for text in texts):
            raise ValueError("Embedding text cannot be empty")

        start = time.time()
        embeddings = await asyncio.to_thread(
            self.model.encode,
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        result = embeddings.tolist()
        logger.info("Generated %s embeddings in %.3fs", len(result), time.time() - start)
        return result

    async def generate_query_embedding(self, query: str) -> List[float]:
        if not query or not query.strip():
            raise ValueError("Empty query provided for embedding")
        return (await self.generate_embeddings([query]))[0]


embedding_service = EmbeddingService()
