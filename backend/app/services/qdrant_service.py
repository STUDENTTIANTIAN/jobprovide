"""Qdrant向量数据库服务
参考: E:\shangagent\data_agent\app\clients\qdrant_client_manager.py
"""
import uuid
from typing import List, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.config import get_settings

settings = get_settings()

# 集合名称
SEGMENT_COLLECTION = "subtitle_segments"
MEDIA_COLLECTION = "media_items"


class QdrantService:
    """Qdrant向量数据库服务"""

    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self._init_client()

    def _init_client(self):
        """初始化Qdrant客户端"""
        if settings.QDRANT_URL:
            self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    async def ensure_collections(self):
        """确保集合存在"""
        if not self.client:
            return

        # 字幕片段集合
        if not await self.client.collection_exists(SEGMENT_COLLECTION):
            await self.client.create_collection(
                collection_name=SEGMENT_COLLECTION,
                vectors_config=VectorParams(
                    size=1024,  # bge-large-zh-v1.5 维度
                    distance=Distance.COSINE
                ),
            )

        # 素材集合
        if not await self.client.collection_exists(MEDIA_COLLECTION):
            await self.client.create_collection(
                collection_name=MEDIA_COLLECTION,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                ),
            )

    async def upsert_segment(
        self,
        segment_id: str,
        embedding: List[float],
        payload: dict
    ):
        """存储字幕片段向量"""
        if not self.client:
            return

        await self.client.upsert(
            collection_name=SEGMENT_COLLECTION,
            points=[
                PointStruct(
                    id=segment_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )

    async def upsert_media(
        self,
        media_id: str,
        embedding: List[float],
        payload: dict
    ):
        """存储素材向量"""
        if not self.client:
            return

        await self.client.upsert(
            collection_name=MEDIA_COLLECTION,
            points=[
                PointStruct(
                    id=media_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )

    async def search_similar_media(
        self,
        query_embedding: List[float],
        score_threshold: float = 0.6,
        limit: int = 3
    ) -> List[dict]:
        """搜索相似素材"""
        if not self.client:
            return []

        result = await self.client.query_points(
            collection_name=MEDIA_COLLECTION,
            query=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )

        return [
            {
                "media_id": point.id,
                "score": point.score,
                "payload": point.payload
            }
            for point in result.points
        ]

    async def search_similar_segments(
        self,
        query_embedding: List[float],
        score_threshold: float = 0.6,
        limit: int = 5
    ) -> List[dict]:
        """搜索相似字幕片段"""
        if not self.client:
            return []

        result = await self.client.query_points(
            collection_name=SEGMENT_COLLECTION,
            query=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )

        return [
            {
                "segment_id": point.id,
                "score": point.score,
                "payload": point.payload
            }
            for point in result.points
        ]

    async def delete_segment(self, segment_id: str):
        """删除字幕片段向量"""
        if not self.client:
            return

        await client.delete(
            collection_name=SEGMENT_COLLECTION,
            points_selector=[segment_id]
        )

    async def delete_media(self, media_id: str):
        """删除素材向量"""
        if not self.client:
            return

        await self.client.delete(
            collection_name=MEDIA_COLLECTION,
            points_selector=[media_id]
        )

    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()


# 全局实例
qdrant_service = QdrantService()
