from typing import List, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.config import get_settings

settings = get_settings()

SEGMENT_COLLECTION = "subtitle_segments"
MEDIA_COLLECTION = "media_items"


class QdrantService:
    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self._init_client()

    def _init_client(self):
        if settings.QDRANT_URL:
            self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    async def ensure_collections(self):
        if not self.client:
            return

        if not await self.client.collection_exists(SEGMENT_COLLECTION):
            await self.client.create_collection(
                collection_name=SEGMENT_COLLECTION,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )

        if not await self.client.collection_exists(MEDIA_COLLECTION):
            await self.client.create_collection(
                collection_name=MEDIA_COLLECTION,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )

    async def upsert_segment(self, segment_id: str, embedding: List[float], payload: dict):
        if not self.client:
            return

        await self.client.upsert(
            collection_name=SEGMENT_COLLECTION,
            points=[PointStruct(id=segment_id, vector=embedding, payload=payload)]
        )

    async def upsert_media(self, media_id: str, embedding: List[float], payload: dict):
        if not self.client:
            return

        await self.client.upsert(
            collection_name=MEDIA_COLLECTION,
            points=[PointStruct(id=media_id, vector=embedding, payload=payload)]
        )

    async def search_similar_media(self, query_embedding: List[float], score_threshold: float = 0.6, limit: int = 3) -> List[dict]:
        if not self.client:
            return []

        result = await self.client.query_points(
            collection_name=MEDIA_COLLECTION,
            query=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )

        return [{"media_id": point.id, "score": point.score, "payload": point.payload} for point in result.points]

    async def search_similar_segments(self, query_embedding: List[float], score_threshold: float = 0.6, limit: int = 5) -> List[dict]:
        if not self.client:
            return []

        result = await self.client.query_points(
            collection_name=SEGMENT_COLLECTION,
            query=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )

        return [{"segment_id": point.id, "score": point.score, "payload": point.payload} for point in result.points]

    async def delete_segment(self, segment_id: str):
        if not self.client:
            return
        await self.client.delete(collection_name=SEGMENT_COLLECTION, points_selector=[segment_id])

    async def delete_media(self, media_id: str):
        if not self.client:
            return
        await self.client.delete(collection_name=MEDIA_COLLECTION, points_selector=[media_id])

    async def close(self):
        if self.client:
            await self.client.close()


qdrant_service = QdrantService()
