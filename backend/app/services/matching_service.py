"""混合匹配服务 - 关键词 + 语义(TEI + Qdrant)
参考: E:\shangagent\data_agent 项目的向量检索方案
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media
from app.models.match_result import MatchResult
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import qdrant_service
from app.config import get_settings

settings = get_settings()


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()

    def keyword_match(self, segment_keywords: List[str], media_tags: List[str]) -> float:
        """关键词匹配（Jaccard相似度）"""
        if not segment_keywords or not media_tags:
            return 0.0
        intersection = set(segment_keywords) & set(media_tags)
        union = set(segment_keywords) | set(media_tags)
        return len(intersection) / len(union) if union else 0.0

    async def semantic_match(self, segment_embedding: List[float], media_embedding: List[float]) -> float:
        """语义匹配（余弦相似度）"""
        if not segment_embedding or not media_embedding:
            return 0.0
        return self.embedding_service.cosine_similarity(segment_embedding, media_embedding)

    def generate_reason(self, matched_keywords: List[str], semantic_score: float) -> str:
        """生成匹配理由"""
        reasons = []
        if matched_keywords:
            reasons.append(f"关键词匹配: {', '.join(matched_keywords)}")
        if semantic_score > 0.8:
            reasons.append("语义高度相关")
        elif semantic_score > 0.6:
            reasons.append("语义相关")
        return " | ".join(reasons) if reasons else "无匹配"

    async def match_segment(self, segment_id: UUID) -> List[dict]:
        """为单个字幕片段匹配素材
        使用Qdrant进行向量检索，提高匹配效率
        """
        from app.models.subtitle_segment import SubtitleSegment

        # 获取字幕片段
        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        if not segment:
            return []

        # 方案A: 使用Qdrant向量检索（推荐）
        if qdrant_service.client and segment.embedding:
            return await self._match_with_qdrant(segment)

        # 方案B: 降级到本地计算
        return await self._match_local(segment)

    async def _match_with_qdrant(self, segment) -> List[dict]:
        """使用Qdrant进行向量检索"""
        from app.models.subtitle_segment import SubtitleSegment

        # 1. 从Qdrant搜索相似素材（向量检索）
        similar_media = await qdrant_service.search_similar_media(
            query_embedding=segment.embedding,
            score_threshold=0.5,  # 降低阈值以获取更多候选
            limit=10
        )

        if not similar_media:
            return []

        # 2. 获取匹配的素材详细信息
        media_ids = [item["media_id"] for item in similar_media]
        media_result = await self.db.execute(
            select(Media).where(Media.id.in_(media_ids))
        )
        media_map = {str(m.id): m for m in media_result.scalars().all()}

        # 3. 计算混合分数
        matches = []
        for item in similar_media:
            media_id = item["media_id"]
            media = media_map.get(media_id)
            if not media:
                continue

            # 关键词匹配
            kw_score = self.keyword_match(
                segment.keywords or [],
                media.tags or []
            )

            # 语义匹配分数（来自Qdrant的余弦相似度）
            sem_score = item["score"]

            # 混合分数
            total_score = (
                settings.KEYWORD_WEIGHT * kw_score +
                settings.SEMANTIC_WEIGHT * sem_score
            )

            # 匹配关键词
            matched_kw = list(set(segment.keywords or []) & set(media.tags or []))

            matches.append({
                "media_id": media.id,
                "score": total_score,
                "keyword_score": kw_score,
                "semantic_score": sem_score,
                "reason": self.generate_reason(matched_kw, sem_score)
            })

        # 排序并返回Top3
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]

    async def _match_local(self, segment) -> List[dict]:
        """本地计算匹配（降级方案）"""
        # 获取所有素材
        media_result = await self.db.execute(select(Media))
        all_media = media_result.scalars().all()

        if not all_media:
            return []

        # 计算匹配分数
        matches = []
        for media in all_media:
            # 关键词匹配
            kw_score = self.keyword_match(
                segment.keywords or [],
                media.tags or []
            )

            # 语义匹配
            sem_score = 0.0
            if segment.embedding and media.embedding:
                sem_score = await self.semantic_match(
                    segment.embedding,
                    media.embedding
                )

            # 混合分数
            total_score = (
                settings.KEYWORD_WEIGHT * kw_score +
                settings.SEMANTIC_WEIGHT * sem_score
            )

            # 匹配关键词
            matched_kw = list(set(segment.keywords or []) & set(media.tags or []))

            matches.append({
                "media_id": media.id,
                "score": total_score,
                "keyword_score": kw_score,
                "semantic_score": sem_score,
                "reason": self.generate_reason(matched_kw, sem_score)
            })

        # 排序并返回Top3
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]

    async def index_segment_to_qdrant(self, segment_id: UUID):
        """将字幕片段索引到Qdrant"""
        from app.models.subtitle_segment import SubtitleSegment

        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        if not segment:
            return

        # 生成embedding
        embedding = await self.embedding_service.get_embedding(segment.content)
        if not embedding:
            return

        # 存储到Qdrant
        await qdrant_service.upsert_segment(
            segment_id=str(segment_id),
            embedding=embedding,
            payload={
                "content": segment.content,
                "keywords": segment.keywords or [],
                "task_id": str(segment.task_id)
            }
        )

    async def index_media_to_qdrant(self, media_id: UUID):
        """将素材索引到Qdrant"""
        result = await self.db.execute(
            select(Media).where(Media.id == media_id)
        )
        media = result.scalar_one_or_none()
        if not media:
            return

        # 拼接文本用于embedding: name + tags
        text_parts = []
        if media.name:
            text_parts.append(media.name)
        if media.tags:
            text_parts.extend(media.tags)
        text = " ".join(text_parts) if text_parts else media.url

        # 生成embedding
        embedding = await self.embedding_service.get_embedding(text)
        if not embedding:
            return

        # 存储到Qdrant
        await qdrant_service.upsert_media(
            media_id=str(media_id),
            embedding=embedding,
            payload={
                "name": media.name,
                "tags": media.tags or [],
                "type": media.type
            }
        )

    async def save_match_results(self, segment_id: UUID, matches: List[dict]) -> List[MatchResult]:
        """保存匹配结果"""
        results = []
        for i, match in enumerate(matches):
            result = MatchResult(
                segment_id=segment_id,
                media_id=match["media_id"],
                score=match["score"],
                keyword_score=match["keyword_score"],
                semantic_score=match["semantic_score"],
                reason=match["reason"],
                rank=i + 1,
                model="hybrid-qdrant" if qdrant_service.client else "hybrid-local"
            )
            self.db.add(result)
            results.append(result)

        await self.db.flush()
        return results

    async def match_task_segments(self, task_id: UUID) -> int:
        """批量匹配任务的所有片段

        Returns:
            int: 匹配的片段数量
        """
        from app.models.subtitle_segment import SubtitleSegment

        # 获取所有片段
        result = await self.db.execute(
            select(SubtitleSegment)
            .where(SubtitleSegment.task_id == task_id)
            .order_by(SubtitleSegment.sort_order)
        )
        segments = result.scalars().all()

        # 为每个片段执行匹配
        matched_count = 0
        for segment in segments:
            try:
                matches = await self.match_segment(segment.id)
                if matches:
                    await self.save_match_results(segment.id, matches)
                    matched_count += 1
            except Exception as e:
                print(f"Match failed for segment {segment.id}: {e}")
                continue

        return matched_count
