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

    def keyword_match(self, segment_keywords: List[str], media_tags: List[str], media_name: str = "") -> float:
        if not segment_keywords:
            return 0.0

        media_text = media_name.lower() if media_name else ""
        media_tags_lower = [t.lower() for t in (media_tags or [])]
        seg_keywords_lower = [k.lower() for k in segment_keywords]

        total_score = 0.0
        for seg_kw in seg_keywords_lower:
            for media_tag in media_tags_lower:
                if seg_kw == media_tag:
                    total_score += 1.0
                elif seg_kw in media_tag or media_tag in seg_kw:
                    total_score += 0.5
            if media_text and seg_kw in media_text:
                total_score += 0.8

        max_possible = len(seg_keywords_lower) * 1.5
        return min(total_score / max_possible, 1.0) if max_possible > 0 else 0.0

    async def semantic_match(self, segment_embedding: List[float], media_embedding: List[float]) -> float:
        if not segment_embedding or not media_embedding:
            return 0.0
        return self.embedding_service.cosine_similarity(segment_embedding, media_embedding)

    def generate_reason(self, matched_keywords: List[str], semantic_score: float) -> str:
        reasons = []
        if matched_keywords:
            reasons.append(f"关键词匹配: {', '.join(matched_keywords[:3])}")
        if semantic_score > 0.8:
            reasons.append("语义高度相关")
        elif semantic_score > 0.6:
            reasons.append("语义相关")
        elif semantic_score > 0.3:
            reasons.append("部分语义相关")
        return " | ".join(reasons) if reasons else "推荐素材"

    async def match_segment(self, segment_id: UUID) -> List[dict]:
        from app.models.subtitle_segment import SubtitleSegment

        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        if not segment:
            return []

        if qdrant_service.client and segment.embedding:
            return await self._match_with_qdrant(segment)

        return await self._match_local(segment)

    async def _match_with_qdrant(self, segment) -> List[dict]:
        from app.models.subtitle_segment import SubtitleSegment

        similar_media = await qdrant_service.search_similar_media(
            query_embedding=segment.embedding,
            score_threshold=0.5,
            limit=10
        )

        if not similar_media:
            return []

        media_ids = [item["media_id"] for item in similar_media]
        media_result = await self.db.execute(
            select(Media).where(Media.id.in_(media_ids))
        )
        media_map = {str(m.id): m for m in media_result.scalars().all()}

        matches = []
        for item in similar_media:
            media_id = item["media_id"]
            media = media_map.get(media_id)
            if not media:
                continue

            kw_score = self.keyword_match(
                segment.keywords or [],
                media.tags or [],
                media.name or ""
            )

            sem_score = item["score"]

            total_score = (
                settings.KEYWORD_WEIGHT * kw_score +
                settings.SEMANTIC_WEIGHT * sem_score
            )

            matched_kw = list(set(segment.keywords or []) & set(media.tags or []))

            matches.append({
                "media_id": media.id,
                "score": total_score,
                "keyword_score": kw_score,
                "semantic_score": sem_score,
                "reason": self.generate_reason(matched_kw, sem_score)
            })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]

    async def _match_local(self, segment) -> List[dict]:
        media_result = await self.db.execute(select(Media))
        all_media = media_result.scalars().all()

        if not all_media:
            return []

        matches = []
        for media in all_media:
            kw_score = self.keyword_match(
                segment.keywords or [],
                media.tags or [],
                media.name or ""
            )

            sem_score = 0.0
            if segment.embedding and media.embedding:
                sem_score = await self.semantic_match(
                    segment.embedding,
                    media.embedding
                )

            total_score = (
                settings.KEYWORD_WEIGHT * kw_score +
                settings.SEMANTIC_WEIGHT * sem_score
            )

            matched_kw = list(set(segment.keywords or []) & set(media.tags or []))

            matches.append({
                "media_id": media.id,
                "score": total_score,
                "keyword_score": kw_score,
                "semantic_score": sem_score,
                "reason": self.generate_reason(matched_kw, sem_score)
            })

        has_matches = any(m["score"] > 0 for m in matches)
        if has_matches:
            matches.sort(key=lambda x: x["score"], reverse=True)
            return matches[:3]
        else:
            import random
            shuffled = list(matches)
            random.shuffle(shuffled)
            return shuffled[:3]

    async def index_segment_to_qdrant(self, segment_id: UUID):
        from app.models.subtitle_segment import SubtitleSegment

        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        if not segment:
            return

        embedding = await self.embedding_service.get_embedding(segment.content)
        if not embedding:
            return

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
        result = await self.db.execute(
            select(Media).where(Media.id == media_id)
        )
        media = result.scalar_one_or_none()
        if not media:
            return

        text_parts = []
        if media.name:
            text_parts.append(media.name)
        if media.tags:
            text_parts.extend(media.tags)
        text = " ".join(text_parts) if text_parts else media.url

        embedding = await self.embedding_service.get_embedding(text)
        if not embedding:
            return

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
        from app.models.subtitle_segment import SubtitleSegment

        result = await self.db.execute(
            select(SubtitleSegment)
            .where(SubtitleSegment.task_id == task_id)
            .order_by(SubtitleSegment.sort_order)
        )
        segments = result.scalars().all()

        matched_count = 0
        for segment in segments:
            try:
                matches = await self.match_segment(segment.id)
                if matches:
                    await self.save_match_results(segment.id, matches)
                    matched_count += 1
            except Exception as e:
                print(f"Match failed: {segment.id}: {e}")
                continue

        return matched_count
