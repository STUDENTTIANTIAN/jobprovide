from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media
from app.models.match_result import MatchResult
from app.services.embedding_service import EmbeddingService
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
        """为单个字幕片段匹配素材"""
        from app.models.subtitle_segment import SubtitleSegment

        # 获取字幕片段
        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        if not segment:
            return []

        # 获取所有素材
        media_result = await self.db.execute(select(Media))
        all_media = media_result.scalars().all()

        if not all_media:
            return []

        # 计算匹配分数
        matches = []
        for media in all_media:
            # 关键词匹配
            kw_score = self.keyword_match(segment.keywords or [], media.tags or [])

            # 语义匹配
            sem_score = 0.0
            if segment.embedding and media.embedding:
                sem_score = await self.semantic_match(segment.embedding, media.embedding)

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
                model="hybrid"
            )
            self.db.add(result)
            results.append(result)

        await self.db.flush()
        return results