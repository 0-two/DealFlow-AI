"""Qdrant vector storage for document indexing and similarity retrieval."""

import asyncio
import hashlib
import logging
import time
import uuid
from collections import OrderedDict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchText,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config.settings import settings
from app.services.embedding_service import embedding_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStoreService:
    """Qdrant-backed vector store with the legacy service interface preserved."""

    COLLECTIONS = ("Investor", "FundingDeal", "PolicyDocument", "NewsArticle", "Startup")

    def __init__(self) -> None:
        if not settings.QDRANT_URL:
            raise ValueError("QDRANT_URL not configured in settings")

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=settings.QDRANT_TIMEOUT_SECONDS,
        )
        self._search_cache: "OrderedDict[str, Tuple[float, List[Dict[str, Any]]]]" = OrderedDict()
        self._search_cache_lock = asyncio.Lock()
        logger.info("Connecting to Qdrant at %s", settings.QDRANT_URL)
        self.initialize_collections()
        logger.info("Qdrant vector store initialized")

    def initialize_collections(self) -> None:
        """Create application collections if they do not already exist."""
        existing = {
            collection.name for collection in self.client.get_collections().collections
        }
        for name in self.COLLECTIONS:
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=embedding_service.dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection %s", name)

    def recreate_collection(self, collection_name: str) -> bool:
        """Delete and recreate one collection. Existing data is permanently deleted."""
        try:
            self.client.delete_collection(collection_name=collection_name)
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_service.dimension,
                    distance=Distance.COSINE,
                ),
            )
            return True
        except Exception as exc:
            logger.error("Error recreating collection %s: %s", collection_name, exc)
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "vector_size": embedding_service.dimension,
            }
        except Exception as exc:
            logger.error("Error getting collection info for %s: %s", collection_name, exc)
            return None

    async def add_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        generate_embeddings: bool = True,
    ) -> bool:
        if not documents or not collection_name:
            return False
        try:
            collections = {
                collection.name for collection in self.client.get_collections().collections
            }
            if collection_name not in collections:
                logger.error("Collection %s does not exist", collection_name)
                return False

            if generate_embeddings:
                contents = [str(document.get("content", "")) for document in documents]
                embeddings = await embedding_service.generate_embeddings(contents)
            else:
                embeddings = [document.get("vector") for document in documents]

            if len(embeddings) != len(documents) or any(not vector for vector in embeddings):
                logger.error("Document/vector count mismatch for %s", collection_name)
                return False

            points = []
            for document, vector in zip(documents, embeddings):
                payload = {
                    key: self._json_value(value)
                    for key, value in document.items()
                    if key != "vector" and not key.startswith("_") and value is not None
                }
                points.append(
                    PointStruct(
                        id=self._point_id(document, payload),
                        vector=vector,
                        payload=payload,
                    )
                )

            batch_size = max(1, settings.QDRANT_UPSERT_BATCH_SIZE)
            total_batches = (len(points) + batch_size - 1) // batch_size
            for batch_number, start in enumerate(range(0, len(points), batch_size), start=1):
                batch = points[start : start + batch_size]
                last_error: Optional[Exception] = None
                for attempt in range(1, 4):
                    try:
                        self.client.upsert(
                            collection_name=collection_name,
                            points=batch,
                            wait=True,
                        )
                        last_error = None
                        break
                    except Exception as exc:
                        last_error = exc
                        if attempt < 3:
                            delay = 2 ** (attempt - 1)
                            logger.warning(
                                "Qdrant upsert batch %s/%s failed (attempt %s/3); "
                                "retrying in %ss: %s",
                                batch_number,
                                total_batches,
                                attempt,
                                delay,
                                exc,
                            )
                            await asyncio.sleep(delay)
                if last_error is not None:
                    raise last_error
                logger.info(
                    "Upserted batch %s/%s (%s documents) into %s",
                    batch_number,
                    total_batches,
                    len(batch),
                    collection_name,
                )
            return True
        except Exception as exc:
            logger.error("Error adding documents to %s: %s", collection_name, exc, exc_info=True)
            return False

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: str = "Startup",
    ) -> List[Dict[str, Any]]:
        """Compatibility method used by the RAG retriever."""
        return await self._search_by_vector(
            collection_name, query_embedding, top_k, filters
        )

    async def hybrid_search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query or not collection_name:
            return []
        cache_key = f"{collection_name}|{limit}|{query.strip()}|{filters or {}}"
        if settings.CACHE_ENABLED:
            async with self._search_cache_lock:
                cached = self._search_cache.get(cache_key)
                if cached and time.time() - cached[0] <= settings.SEARCH_CACHE_TTL_SECONDS:
                    self._search_cache.move_to_end(cache_key)
                    return cached[1]

        query_vector = await embedding_service.generate_query_embedding(query)
        results = await self._search_by_vector(collection_name, query_vector, limit, filters)

        if settings.CACHE_ENABLED:
            async with self._search_cache_lock:
                self._search_cache[cache_key] = (time.time(), results)
                self._search_cache.move_to_end(cache_key)
                while len(self._search_cache) > settings.SEARCH_CACHE_MAX_ENTRIES:
                    self._search_cache.popitem(last=False)
        return results

    async def _search_by_vector(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        try:
            response = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=self._build_filter(filters),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {
                    "uuid": str(point.id),
                    "properties": point.payload or {},
                    "score": float(point.score),
                    **(point.payload or {}),
                }
                for point in response.points
            ]
        except Exception as exc:
            logger.error("Qdrant search error in %s: %s", collection_name, exc)
            return []

    @staticmethod
    def _build_filter(filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        if not filters:
            return None
        conditions = []
        field_map = {
            "sector": "focus_areas",
            "location": "location",
            "stage": "stages",
            "investor_type": "type",
        }
        for key, value in filters.items():
            if not value or key not in field_map:
                continue
            field = field_map[key]
            if isinstance(value, list):
                conditions.append(FieldCondition(key=field, match=MatchAny(any=value)))
            elif key == "location" or key == "investor_type":
                conditions.append(FieldCondition(key=field, match=MatchText(text=str(value))))
            else:
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
        return Filter(must=conditions) if conditions else None

    @staticmethod
    def _point_id(document: Dict[str, Any], payload: Dict[str, Any]) -> str:
        source_id = document.get("id") or document.get("uuid") or payload.get("name")
        if source_id is None:
            source_id = repr(sorted(payload.items()))
        return str(uuid.uuid5(uuid.NAMESPACE_URL, hashlib.sha256(str(source_id).encode()).hexdigest()))

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            return value
        return str(value)

    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        for name in self.COLLECTIONS:
            info = self.get_collection_info(name)
            if info:
                stats[name] = info
        return {"collections": stats}

    def close(self) -> None:
        self.client.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


try:
    vector_store_service = VectorStoreService()
except Exception as exc:
    logger.error("Failed to initialize vector_store_service: %s", exc)
    vector_store_service = None
